import json

from cartographer.exceptions.request_exceptions import DataMissing, BadPageCountParameter, BadPageCursorParameter, \
    BadPageOffsetParameter
from cartographer.requests.jsonapi_request_interface import JSONAPIRequestInterface
from cartographer.utils.version import JSONAPIVersion, JSONAPI_DEFAULT_VERSION


class JSONAPIFlaskRequestMixin(JSONAPIRequestInterface):
    def get_jsonapi_data(self):
        if self.json and self.json.get('data'):
            data = self.json.get('data')
        elif self.form and self.form.get('data'):
            data_str = self.form.get('data')
            data = json.loads(data_str)
        else:
            raise DataMissing()
        # TODO: have get_data clients expect attributes to be nested
        if self.get_json_api_version() == JSONAPIVersion.JSON_API_1_0:
            data.update(data.get('attributes', {}))
        return data

    def get_sort(self):
        return self.args.get('sort')

    def get_pagination(self, page_count_default=10, cursor_formatter=None):
        per_page = self.args.get('page[count]')
        if per_page is not None:
            if not (isinstance(per_page, str) and per_page == 'infinity'):
                try:
                    per_page = int(per_page)
                except TypeError:
                    raise BadPageCountParameter(per_page)
        else:
            per_page = page_count_default

        page_cursor = self.args.get('page[cursor]')
        if page_cursor is not None and cursor_formatter is not None:
            try:
                page_cursor = cursor_formatter(page_cursor)
            except:
                raise BadPageCursorParameter(page_cursor)

        page_offset = self.args.get('page[offset]')
        if page_offset is not None:
            try:
                page_offset = int(page_offset)
            except TypeError:
                raise BadPageOffsetParameter(page_offset)

        return page_cursor, page_offset, per_page

    def get_includes(self):
        """Returns a list of the requested resources to include in the response for this request."""
        includes_string = self.args.get('include')
        if includes_string:
            if includes_string in ['null', 'none', '[]']:
                return []
            else:
                return includes_string.split(',')
        else:
            return None

    def get_requested_fields(self):
        """Returns a list of the requested attributes to include in the response for this request."""
        type_to_list = self.dictionary_from_get('fields')
        return {key: val.split(',') for key, val in type_to_list.items()}

    def get_included(self):
        """Returns a list of the included resources sent from the client"""
        if not self.json:
            raise DataMissing()
        return self.json.get('included', [])

    def get_included_with_filter(self, type_, id_=None):
        included = self.get_included()
        return [
            resource
            for resource in included
            if resource.get('type') == type_
            and (id_ is None or id_ == resource.get('id'))
        ]

    def get_filters(self):
        return self.dictionary_from_get('filter')

    def get_bool(self, key):
        val = self.args.get(key)
        if val is None:
            return None
        return bool(str(val).lower() not in ['false', '0'])

    def get_json_api_version(self, default_version=None):
        if default_version is None:
            default_version = JSONAPI_DEFAULT_VERSION
        return self.args.get('json-api-version', default_version)
