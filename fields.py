""" slog: Simple sample tracker system.

Data field classes.

Per Kraulis
2011-02-09
"""

import logging, copy

from HyperText.HTML40 import *

from wireframe.response import *

from . import configuration, utils


class Field(object):
    "Abstract data field."

    def __init__(self, name,
                 required=False, fixed=False, default=None,
                 description=None):
        self.name = name
        self.required = required
        self.fixed = fixed
        self.default = default
        self.description = description

    def get_description(self):
        "Return the description text formatted to HTML."
        return utils.rst_to_html(self.description)

    def get_editable(self, dispatcher, user):
        """Is the field in the dispatcher editable for the given user?
        If fixed, then disallowed if value is other than None.
        By default, the same rights as for the dispatcher."""
        if self.fixed:
            try:
                if dispatcher.doc.get(self.name) is not None: return False
            except AttributeError:
                pass
        return dispatcher.get_editable(user)

    def check_editable(self, dispatcher, user):
        if not self.get_editable(dispatcher, user):
            raise HTTP_FORBIDDEN("Field '%s' may not edited by '%s'."
                                 % (self.name, entity.user))

    def get_edit_button(self, dispatcher):
        if self.get_editable(dispatcher, dispatcher.user):
            return FORM(INPUT(type='hidden', name='edit', value=self.name),
                        INPUT(type='submit', value='Edit'),
                        method='GET',
                        action=dispatcher.get_url())
        else:
            return ''

    def get_view(self, entity):
        value = entity.doc.get(self.name)
        if value is None: return ''
        return value

    def get_edit_form(self, entity):
        return FORM(TABLE(
            TR(TH(self.name),
               TD(self.get_edit_form_field(entity)),
               TD(I(self.required and 'required' or 'optional')),
               TD(self.get_description())),
            TR(TD(),
               TD(INPUT(type='submit', value='Save'),
                  INPUT(type='hidden', name='_rev', value=entity.doc.rev)))),
                    method='POST',
                    action=entity.get_url())

    def get_edit_form_field(self, entity):
        "Return the HTML element for editing the current value."
        raise NotImplementedError

    def value_to_string(self, value):
        "Convert the value to string for the edit form field."
        if value is None:
            return ''
        else:
            return str(value)

    def get_create_form_field(self, dispatcher):
        "Return the HTML element for creating the value for a new entity."
        return self.get_edit_form_field(dispatcher)

    def get_value(self, dispatcher, request, required=True):
        """Get the value for the field from the CGI form inputs.
        Raise KeyError if no such named field in the CGI form inputs
        and 'required' is True, else try to use the value None.
        Raise ValueError if invalid value for the field."""
        try:
            value = request.cgi_fields[self.name].value
        except KeyError:
            if required:
                raise
            else:
                value = None
        else:
            value = value.strip()
            if not value:
                value = None
            elif value == '__none__':
                value = None
        return self.check_value(dispatcher, value)

    def check_value(self, dispatcher, value):
        """Check that the value is valid, else raise ValueError.
        Return the value, possibly converted to the appropriate type."""
        if value is None and self.required:
            raise ValueError("Value for '%s' must be non-null." % self.name)
        return value


class StringField(Field):
    "Field for a one-line text string."

    def __init__(self, name,
                 required=False, fixed=False, default=None,
                 size=20, maxlength=255, description=None):
        super(StringField, self).__init__(name,
                                          required=required,
                                          fixed=fixed,
                                          default=default,
                                          description=description)
        self.size = size
        self.maxlength = maxlength

    def get_edit_form_field(self, entity):
        try:
            value = self.value_to_string(entity.doc.get(self.name))
        except AttributeError:          # '.doc' not set when creating
            value = ''
        if not value and self.default:
            if callable(self.default):
                value = self.default(entity)
            else:
                value = self.default
        return INPUT(type='text', name=self.name, value=value,
                     size=self.size, maxlength=self.maxlength)


class TextField(Field):
    "Field for a multi-line text string. Assumed to be reStructuredText."

    def __init__(self, name,
                 required=False, fixed=False, default=None,
                 rows=4, cols=80, description=None):
        super(TextField, self).__init__(name,
                                        required=required,
                                        fixed=fixed,
                                        default=default,
                                        description=description)
        self.rows = rows
        self.cols = cols

    def get_view(self, entity):
        value = entity.doc.get(self.name)
        if value is None: return ''
        return utils.rst_to_html(value)

    def get_edit_form_field(self, entity):
        try:
            value = self.value_to_string(entity.doc.get(self.name))
        except AttributeError:          # '.doc' not set when creating
            value = ''
        return TEXTAREA(value, name=self.name, rows=self.rows, cols=self.cols)

    def check_value(self, dispatcher, value):
        "Convert to sensible newlines."
        value = super(TextField, self).check_value(dispatcher, value)
        if value is None: return None
        return value.replace('\r\n', '\n')


class FloatField(StringField):
    "Field to represent a floating point value."

    def value_to_string(self, value):
        "Convert the value to string for the edit form field."
        if value is None:
            return ''
        else:
            return "%g" % value

    def check_value(self, dispatcher, value):
        value = super(FloatField, self).check_value(dispatcher, value)
        if value is None: return None
        try:
            return float(value)
        except ValueError:
            raise ValueError("Value for '%s' is not a float." % self.name)


class IntegerField(StringField):
    "Field to represent an integer value."

    def value_to_string(self, value):
        "Convert the value to string for the edit form field."
        if value is None:
            return ''
        else:
            return str(value)

    def check_value(self, dispatcher, value):
        value = super(IntegerField, self).check_value(dispatcher, value)
        if value is None: return None
        try:
            return int(value)
        except ValueError:
            raise ValueError("Value for '%s' is not an integer." % self.name)


class PositiveIntegerField(IntegerField):
    "Field to represent a positive integer value."

    def check_value(self, dispatcher, value):
        value = super(PositiveIntegerField, self).check_value(dispatcher, value)
        if value is None: return None
        try:
            value = int(value)
            if value <= 0: raise ValueError
        except ValueError:
            raise ValueError("Value for '%s' is not a positive integer."
                             % self.name)
        return value


class BooleanField(Field):
    "Field to represent a boolean value, e.g. 'true' or 'false'."

    def get_edit_form_field(self, entity):
        try:
            value = entity.doc.get(self.name)
        except AttributeError:          # '.doc' not set when creating
            value = None
        rows = []
        attrs = dict(type='radio', name=self.name)
        if not self.required:
            attrs['value'] = '__none__'
            if value is None: attrs['checked'] = True
            rows.append(TR(TD(INPUT(**attrs), B('Undefined'))))
        attrs['value'] = 'false'
        if value == False:
            attrs['checked'] = True
        else:
            attrs.pop('checked', None)
        rows.append(TR(TD(INPUT(**attrs), B('False'))))
        attrs['value'] = 'true'
        if value == True:
            attrs['checked'] = True
        else:
            attrs.pop('checked', None)
        rows.append(TR(TD(INPUT(**attrs), B('True'))))
        return TABLE(*rows)

    def check_value(self, dispatcher, value):
        value = super(BooleanField, self).check_value(dispatcher, value)
        if value is None: return None
        value = value.lower()
        if value in ('true', 'on', 'yes'):
            return True
        elif value in ('false', 'off', 'no'):
            return False
        else:
            raise ValueError("Value for '%s' is not a boolean." % self.name)


class TimestampField(StringField):
    "Field to represent an ISO format date-time value."

    def get_edit_form_field(self, entity):
        try:
            value = self.value_to_string(entity.doc.get(self.name))
        except AttributeError:          # '.doc' not set when creating
            value = ''
        return TABLE(TR(TD(INPUT(type='checkbox', name=self.name, value='now'),
                           B('Now')),
                        TD('Overrides text input below.')),
                     TR(TD(INPUT(type='text', name=self.name, value=value,
                                 size=20, maxlength=20)),
                        TD('ISO format, e.g. 2011-02-09T09:23:34Z')))

    def get_value(self, dispatcher, request, required=True):
        values = request.cgi_fields.getlist(self.name)
        if values:
            for value in values:
                if value == 'now':
                    value = utils.now_iso()
                    break
            else:
                if not value.strip():
                    value = None
        else:
            if required:
                raise KeyError
            else:
                value = None
        return self.check_value(dispatcher, value)

    def check_value(self, dispatcher, value):
        value = super(TimestampField, self).check_value(dispatcher, value)
        if value is None: return value
        try:
            utils.parse_iso_datetime(value)
        except ValueError:
            raise ValueError('datetime value does not have valid ISO format')
        return value


class NameField(StringField):
    "Field for a name, which is an identifier-like string."

    def __init__(self, name,
                 required=True, fixed=False, default=None,
                 size=20, maxlength=255, description=None):
        super(NameField, self).__init__(name,
                                        required=required,
                                        fixed=fixed,
                                        default=default,
                                        size=size,
                                        maxlength=maxlength,
                                        description=description)

    def check_value(self, dispatcher, value):
        """A name must be one word containing only alphanumerical
        characters, or (in any position except the first) underscore '_'.
        In particular, no blank may be present.
        It must be unique for its entity type."""
        value = super(NameField, self).check_value(dispatcher, value)
        if value is None: return value
        if not configuration.VALID_NAME_RX.match(value):
            raise ValueError("Value '%s' for '%s' is not a valid name"
                             % (value, self.name))
        try:
            current = dispatcher.doc.get(self.name)
        except AttributeError:      # No 'doc' in dispatcher when creating
            pass
        else:
            if value != current:
                entity = dispatcher.__class__.__name__.lower()
                view = dispatcher.db.view("%s/name" % entity)
                if view[value]:
                    raise ValueError("Value '%s' for '%s' is not unique."
                                     % (value, self.name))
        return value


class OptionField(StringField):
    "Field to represent selection of one option."

    def __init__(self, name, options,
                 required=False, default=None,
                 description=None):
        super(OptionField, self).__init__(name,
                                          required=required,
                                          default=default,
                                          description=description)
        self.options = list(options)

    def get_edit_form_field(self, entity):
        if self.default:
            if callable(self.default):
                value = self.default(entity)
            else:
                value = self.default
        else:
            try:
                value = entity.doc.get(self.name)
            except AttributeError:      # '.doc' not set when creating
                value = None
        options = []
        for opt in self.options:
            if opt == value:
                options.append(OPTION(opt, selected=True))
            else:
                options.append(OPTION(opt))
        return SELECT(name=self.name, *options)


class PasswordField(StringField):
    "String field for a password, stored as its MD5 hexdigest."

    def __init__(self, name,
                 description='Account password.'):
        super(PasswordField, self).__init__(name,
                                            required=True,
                                            description=description)

    def get_view(self, entity):
        return I('[password]')

    def get_edit_form_field(self, entity):
        return TABLE(TR(TD('new', klass='right'),
                        TD(INPUT(type='password', name="new_%s" % self.name,
                                 size=self.size, maxlength=self.maxlength))),
                     TR(TD('confirm', klass='right'),
                        TD(INPUT(type='password', name="confirm_%s" % self.name,
                                 size=self.size, maxlength=self.maxlength))))

    def get_value(self, dispatcher, request, required=True):
        """Get the value for the field from the CGI form inputs.
        Return the 'new' and 'confirm' values in a dictionary.
        Raise KeyError if no such named field in the CGI form inputs
        and 'required' is True, else try to use the value None.
        Raise ValueError if invalid value for the field."""
        result = dict()
        for part in ['new', 'confirm']:
            try:
                key = "%s_%s" % (part, self.name)
                value = request.cgi_fields[key].value.strip()
                if not value: raise KeyError
            except KeyError:
                pass
            else:
                result[part] = value
        if not result:
            raise KeyError
        return self.check_value(dispatcher, result)

    def check_value(self, dispatcher, value):
        """Check the 'new' and 'confirm' values.
        Convert and return the password as its MD5 hexdigest value."""
        try:
            new = value['new']
        except KeyError:
            if self.required:
                raise ValueError("Value for '%s' be must non-null." % self.name)
        confirm = value.get('confirm')
        if new != confirm:
            raise ValueError('new and confirm values do not match')
        return utils.hexdigest(new)


class ReferenceField(Field):
    "Reference to an entity of a specified type."

    def __init__(self, name, referred,
                 required=False, fixed=False, default=None,
                 description=None):
        super(ReferenceField, self).__init__(name,
                                             required=required,
                                             fixed=fixed,
                                             default=default,
                                             description=description)
        self.referred = referred.lower()

    def get_view(self, entity):
        name = entity.doc.get(self.name)
        if name is None:
            return ''
        else:
            return A(name, href=configuration.get_url(self.referred, name))

    def get_edit_form_field(self, entity):
        try:
            value = entity.doc.get(self.name)
        except AttributeError:          # '.doc' not set when creating
            value = self.default
        # XXX how to filter the set of referenced entities appropriately?
        if self.required:
            options = []
        else:
            if value is None:
                options = [OPTION('', value='__none__', selected=True)]
            else:
                options = [OPTION('', value='__none__')]
        for result in entity.db.view("%s/name" % self.referred):
            if result.key == value:
                options.append(OPTION(result.key, selected=True))
            else:
                options.append(OPTION(result.key))
        return SELECT(name=self.name, *options)


class ReferenceListField(ReferenceField):
    "List of references to entities of a specified type."

    def get_view(self, entity):
        names = entity.doc.get(self.name)
        if not names:
            return ''
        else:
            return TABLE(*[TR(TD(A(n, href=configuration.get_url(self.referred,
                                                                 n))))
                           for n in names])

    def get_edit_form_field(self, entity):
        try:
            names = entity.doc.get(self.name) or []
        except AttributeError:          # '.doc' not set when creating
            names = []
        current = set(names)
        options = []
        view = entity.db.view("%s/name" % self.referred)
        for row in view:
            if row.key not in current:
                options.append(OPTION(row.key))
        add = SELECT(name="%s_add" % self.name, size=4, multiple=True, *options)
        remove = TABLE(*[TR(TD(INPUT(type='checkbox',
                                     name="%s_remove" % self.name,
                                     value=name)),
                            TD(name))
                         for name in names])
        return TABLE(TR(TH('Add entities'),
                        TD(add)),
                     TR(TH('Remove entities'),
                        TD(remove)),
                     border=1)

    def get_value(self, dispatcher, request, required=True):
        try:
            names = set(dispatcher.doc.get(self.name) or [])
        except AttributeError:          # When creating
            names = set()
        orig_names = set(names)
        for value in request.cgi_fields.getlist("%s_remove" % self.name):
            names.discard(value.strip())
        for value in request.cgi_fields.getlist("%s_add" % self.name):
            names.add(value.strip())
        names = self.check_value(dispatcher, names)
        if set(names) == orig_names:
            raise KeyError("entities '%s' not changed" % self.name)
        return names

    def check_value(self, dispatcher, value):
        "Convert to list of entity names, and check that they exist."
        names = list(value)
        for name in names:
            try:
                dispatcher.get_named_document(self.referred, name)
            except ValueError:
                raise ValueError("entity '%s' does not exist" % name)
        return names


class SampleSetField(Field):
    "Set of sample references; for Workset."

    def get_view(self, entity):
        samples = entity.doc.get(self.name)
        if not samples: return ''
        rows = [TR(TH('Sample'),
                   TH('Customername'),
                   TH('Grid'),
                   TH('Multiplex label (sequence)'))]
        # Ugly kludge: values from another entity field, via entity method
        try:
            arranged_samples = entity.get_arranged_samples()
        except AttributeError:
            arranged_samples = dict()
        for sample in samples:
            doc = entity.get_named_document('sample', sample)
            url = configuration.get_url('sample', sample)
            multiplex = doc.get('multiplex_label') or ''
            value = doc.get('multiplex_sequence')
            if value: multiplex += " (%s)" % value
            coordinate = arranged_samples.get(sample, '')
            if coordinate:
                coordinate = utils.grid_coordinate(*coordinate)
            rows.append(TR(TD(A(sample, href=url)),
                           TD(doc.get('customername') or ''),
                           TD(coordinate),
                           TD(multiplex)))
        return TABLE(border=1, *rows)

    def get_edit_form_field(self, entity):
        from .sample import Sample
        try:
            samples = entity.doc.get(self.name)
            if not samples: raise AttributeError
        except AttributeError:
            remove = ''
        else:
            rows = [TR(TH('Sample', colspan=2),
                       TH('Customername'),
                       TH('Grid'),
                       TH('Multiplex'))]
            # Ugly kludge: values from another entity field, via entity method
            try:
                arranged_samples = entity.get_arranged_samples()
            except AttributeError:
                arranged_samples = dict()
            for sample in samples:
                doc = entity.get_named_document('sample', sample)
                multiplex = []
                value = doc.get('multiplex_label')
                if value: multiplex.append(value)
                value = doc.get('multiplex_sequence')
                if value: multiplex.append(value)
                coordinate = arranged_samples.get(sample, '')
                if coordinate:
                    coordinate = utils.grid_coordinate(*coordinate)
                rows.append(TR(TD(INPUT(type='checkbox',
                                        name="%s_remove" % self.name,
                                        value=sample)),
                               TD(sample),
                               TD(doc.get('customername') or ''),
                               TD(coordinate),
                               TD(' = '.join(multiplex))))
            remove = TABLE(border=1, *rows)
        rows = [TR(TH('Remove samples'),
                   TD(remove),
                   TD('Check sample(s) to remove from this workset.')),
                TR(TH('Add samples'),
                   TD(TEXTAREA(rows=2, cols=40, name='samples')),
                   TD('Comma-delimited list of samples to add.')),
                TR(TH('Add project'),
                   TD(INPUT(type='text', name='project')),
                   TD('Project whose samples to add.')),
                TR(TH('Add workset'),
                   TD(INPUT(type='text', name='workset')),
                   TD('Workset whose samples to add to this workset.')),
                TR(TH('Remove workset'),
                   TD(INPUT(type='text', name='workset_remove')),
                   TD('Workset whose samples to remove from this workset.'))]
        return TABLE(border=1, *rows)

    def get_value(self, dispatcher, request, required=False):
        # Get already included samples
        try:
            orig_samples = set(dispatcher.doc[self.name])
        except (AttributeError, KeyError, TypeError):
            orig_samples = set()
        updated_samples = orig_samples.copy()

        # Add explicitly given samples
        try:
            samples = request.cgi_fields['samples'].value.strip()
            samples = samples.replace(',', ' ')
            samples = samples.split()
        except KeyError:
            pass
        else:
            updated_samples.update(samples)

        # Add samples from given project, if any
        try:
            project = request.cgi_fields['project'].value.strip()
            if project is None: raise KeyError
        except (KeyError, ValueError):
            pass
        else:
            view = dispatcher.db.view('sample/project')
            updated_samples.update([r.value for r in view[project]])

        # Add samples from given workset, if any
        try:
            workset = request.cgi_fields['workset'].value.strip()
            if not workset: raise KeyError
            if workset == dispatcher.doc['name']: raise KeyError # Skip itself
            workset = dispatcher.get_named_document('workset', workset)
        except (KeyError, ValueError):
            pass
        else:
            updated_samples.update(workset.get('samples') or []) # May be None

        # Remove samples from given workset
        try:
            workset = request.cgi_fields['workset_remove'].value.strip()
            if not workset: raise KeyError
            if workset == dispatcher.doc['name']: raise KeyError # Skip itself
            workset = dispatcher.get_named_document('workset', workset)
        except (KeyError, ValueError):
            pass
        else:
            samples = workset.get('samples') or [] # May be None
            for sample in samples:
                updated_samples.discard(sample)

        # Remove samples one by one
        for sample in request.cgi_fields.getlist("%s_remove" % self.name):
            updated_samples.discard(sample)

        # Check that samples in workset actually exist
        view = dispatcher.db.view('sample/name')
        for sample in list(updated_samples):
            if not view[sample]:
                updated_samples.discard(sample)

        # If no change, then act as if this CGI input was not present at all
        if orig_samples == updated_samples:
            raise KeyError("SampleSet '%s' not changed" % self.name)

        samples = list(updated_samples)
        samples.sort()
        return self.check_value(dispatcher, samples)

    def check_value(self, dispatcher, value):
        "Remove any non-present samples in the grid of the entity."
        try:
            dispatcher.cleanup_arranged_samples(value)
        except AttributeError:
            pass
        return value


class SampleGridField(Field):
    "Field containing the dimensions and arrangement of the sample grid."

    def get_view(self, entity):
        grid = entity.doc.get(self.name) or dict()
        arrangement = grid.get('arrangement')
        if arrangement:                 # Rows of columns of multiplex
            cells = [TD()]
            cells.extend([TH(utils.grid_coordinate(column=j))
                          for j in xrange(len(arrangement[0]))])
            rows = [TR(*cells)]
            for i, row in enumerate(arrangement):
                columns = [TH(utils.grid_coordinate(row=i))]
                for j, column in enumerate(row):
                    multiplex = []
                    for k, sample in enumerate(column):
                        if sample is None:
                            item = '-'
                        else:
                            url = configuration.get_url('sample', sample)
                            item = A(sample, href=url)
                        multiplex.append(TR(TD(item)))
                    columns.append(TD(TABLE(*multiplex)))
                rows.append(TR(*columns))
            return TABLE(border=1, *rows)
        else:
            return I('Undefined arrangement.')

    def get_edit_form_field(self, entity):
        # Get all samples for this workset.
        # Ugly kludge: values from another entity field, via entity method.
        try:
            all_samples = entity.get_all_samples()
        except AttributeError:
            all_samples = set()
        # Get samples already arranged, and not.
        arranged_samples = set(entity.get_arranged_samples().keys())
        unarranged_samples = list(all_samples.difference(arranged_samples))
        unarranged_samples.sort()

        grid = entity.doc.get(self.name) or dict()
        trows = []
        for key in ['rows', 'columns', 'multiplex']:
            trows.append(TR(TH("# %s" % key),
                            TD(INPUT(type='text', size=4,
                                     name="%s_%s" % (self.name, key),
                                     value=str(grid.get(key, ''))))))
        arrangement = grid.get('arrangement')
        if arrangement:                 # Rows of columns of multiplex
            size = max(2, grid['multiplex'])
            cells = [TD()]
            cells.extend([TH(utils.grid_coordinate(column=j))
                          for j in xrange(len(arrangement[0]))])
            rows = [TR(*cells)]
            for i, row in enumerate(arrangement):
                columns = [TH(utils.grid_coordinate(row=i))]
                for j, column in enumerate(row):
                    options = [OPTION(s, selected=True)
                               for s in column if s is not None]
                    options.extend([OPTION(s) for s in unarranged_samples])
                    name = "%s_arrangement_%s_%s" % (self.name, i+1, j+1)
                    # Web browser interface: only multiple allows de-selecting
                    columns.append(TD(SELECT(name=name, size=size,
                                             multiple=True, *options)))
                rows.append(TR(*columns))
            trows.append(TR(TH('arrangement'),
                            TD(TABLE(border=1, *rows))))
        else:
            trows.append(TR(TH('arrangement'),
                            TD(I('undefined'))))
        return TABLE(*trows)

    def get_create_form_field(self, dispatcher):
        "For simplicity, set arrangement as undefined initially."
        return I('Initially undefined arrangement.')

    def get_value(self, dispatcher, request, required=False):
        "Define the arrangement, and optionally resize the grid."
        try:
            doc = dispatcher.doc
        except AttributeError:          # Undefined when creating the entity.
            return dict()
        current = doc.get(self.name) or dict()
        result = dict()
        # Put samples into arrangement, if any
        arrangement = current.get('arrangement')
        if arrangement:
            number = current['multiplex']
            result['arrangement'] = arrangement = copy.deepcopy(arrangement)
            for i, row in enumerate(arrangement):
                for j, column in enumerate(row):
                    name = "%s_arrangement_%s_%s" % (self.name, i+1, j+1)
                    samples = list(request.cgi_fields.getlist(name))
                    if len(samples) > number:
                        samples = samples[:number]
                    elif len(samples) < number:
                        samples.extend([None] * (number - len(samples)))
                    arrangement[i][j] = samples
        # Grid dimensions
        for key in ['rows', 'columns', 'multiplex']:
            try:
                name = "%s_%s" % (self.name, key)
                value = request.cgi_fields[name].value.strip()
                if not value: raise KeyError
                value = int(value)
                if value <= 0: raise ValueError
            except KeyError:
                raise               # Indicates
            except ValueError:      # Invalid value: interpret as None
                result[key] = None
            else:
                result[key] = value
        return self.check_value(dispatcher, result)

    def check_value(self, dispatcher, value):
        """Resize the grid if the dimensions have changed, which may
        exclude some samples from the arrangement.
        Note that samples may be present in more than one place in
        the arrangement."""
        current = dispatcher.doc.get(self.name) or dict()
        current_rows = current.get('rows')
        current_columns = current.get('columns')
        current_multiplex = current.get('multiplex')
        arrangement = value.get('arrangement')
        # Remove arrangement if any dimension us undefined
        new_rows = value.get('rows')
        new_columns = value.get('columns')
        new_multiplex = value.get('multiplex')
        if (new_rows is None) or \
           (new_columns is None) or \
           (new_multiplex is None):
            arrangement = None
        # No existing arrangement; create it
        elif arrangement is None:
            arrangement = [[[None] * new_multiplex] * new_columns] * new_rows
        # Resize if dimensions are defined
        elif (current_rows != new_rows) or \
             (current_columns != new_columns) or \
             (current_multiplex != new_multiplex):
            if new_multiplex > current_multiplex:
                for i in xrange(len(arrangement)):
                    for j in xrange(len(arrangement[i])):
                        arrangement[i][j].extend([None] * (new_multiplex - current_multiplex))
            elif new_multiplex < current_multiplex:
                for i in xrange(len(arrangement)):
                    for j in xrange(len(arrangement[i])):
                        arrangement[i][j] = arrangement[i][j][:new_multiplex]
            if new_columns > current_columns:
                for i in xrange(len(arrangement)):
                    arrangement[i].extend([[None] * new_multiplex] * (new_columns - current_columns))
            elif new_columns < current_columns:
                for i in xrange(len(arrangement)):
                    arrangement[i] = arrangement[i][:new_columns]
            if new_rows > current_rows:
                arrangement.extend([[[None] * new_multiplex] * new_columns] * (new_rows - current_rows))
            elif new_rows < current_rows:
                arrangement = arrangement[:new_rows]
        if arrangement is None:
            try:
                del value['arrangement']
            except KeyError:
                pass
        else:
            value['arrangement'] = arrangement
        return value
