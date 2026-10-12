import openpyxl

class AbstractParser:
    def parse(self, file_path, config):
        raise NotImplementedError("Subclasses must implement parse()")

    def apply_transform(self, value, transform):
        raise NotImplementedError("Subclasses must implement apply_transform()")


class XlsxParser(AbstractParser):
    def parse(self, file_path, config):
        file_rules = config.get('file_rules', {})
        quantity_rows = file_rules.get('quantity_rows', None)    
        sheet_id = file_rules.get('sheet', 0)
        skip_rows = file_rules.get('skip_rows', 0)
        target_model = file_rules.get('target_model', '')
        column_mapping = config.get('column_mapping', {})
        ignore_columns = {item['column'] for item in column_mapping if item.get('type') == 'ignore'}
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        sheet = workbook.worksheets[sheet_id]

        result = []
        self.headers = {}
        header_row = None
        if skip_rows >= 0:
            header_cells = list(sheet.iter_rows(min_row=1, values_only=True))
            if header_cells:
                header_row = header_cells[0]
        if header_row:
            for col_idx, value in enumerate(header_row, start=1):
                if value is not None and str(value).strip():
                    col_letter = openpyxl.utils.get_column_letter(col_idx)
                    self.headers[col_letter] = str(value).strip()
                else:
                    self.headers = {}

        for row_id, row in enumerate(sheet.iter_rows(values_only=True), start=1):

            if row_id <= skip_rows: 
                continue
            
            row_dict = {}          

            for item in column_mapping:
                col_letter = item.get('column')
                field = item.get('field')
                delimiter = item.get('delimiter', '-')
                default_value = 'ЗИП'
                
                if col_letter in ignore_columns:
                    continue 

                col_id = openpyxl.utils.column_index_from_string(col_letter) - 1

                if col_id < len(row):
                    value = row[col_id]
                    if item.get('type') == 'column_parsing':
                        to_parse = item.get('to_parse')
                        transformed = self.apply_transform(value, delimiter, to_parse)
                        
                        if to_parse and isinstance(transformed, dict):
                            prefix = field.rsplit('.', 1)[0] if '.' in field else field
                            for key in to_parse:
                                row_dict[f"{prefix}.{key}"] = transformed.get(key)

                        else:
                            # если to_parse не задан, разворачиваем все ключи словаря 
                            if isinstance(transformed, dict):
                                prefix = field.rsplit('.', 1)[0] if '.' in field else field
                                for key, value in transformed.items():
                                    row_dict[f"{prefix}.{key}"] = value
                            else:
                                row_dict[field] = transformed if transformed else {}
                    else:
                        row_dict[field] = value if value else {}

                    check_dict={k: v for k, v in row_dict.items() if k != 'id'}
            if not any(v is not None and str(v).strip() != '' for v in check_dict.values()):
                continue

            result.append(row_dict)

            if quantity_rows and row_id > quantity_rows + skip_rows:
                break
        return result


    def apply_transform(self, value, delimiter, keys):
        if isinstance(value, str) and delimiter:
            parts = [p.strip() for p in value.split(delimiter) if p.strip()]
            if len(parts) >=3:
                # keys = ['rack', 'shelf', 'place', 'placement']
                return dict(zip(keys, parts))
        return value
