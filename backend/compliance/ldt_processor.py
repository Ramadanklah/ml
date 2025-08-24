"""
LDT Processor for KBV LDT 3.2.19 (German Laboratory Data Transfer Standard)
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class LDTField:
    """Represents a field in the LDT format"""
    name: str
    length: int
    required: bool
    description: str
    example: str


@dataclass
class LDTRecord:
    """Represents a record in the LDT format"""
    record_type: str
    fields: List[LDTField]
    description: str


class LDTProcessor:
    """Processes LDT files according to KBV LDT 3.2.19 specification"""
    
    # LDT 3.2.19 Record Types
    RECORD_TYPES = {
        '01': 'Patient Data',
        '02': 'Order Data',
        '03': 'Result Data',
        '04': 'Comment Data',
        '05': 'End of Order',
        '06': 'End of Patient',
        '07': 'End of File'
    }
    
    def __init__(self):
        self.patients = []
        self.orders = []
        self.results = []
        self.comments = []
        self.errors = []
    
    def parse_ldt_file(self, file_path: str) -> Dict:
        """Parse an LDT file and return structured data"""
        try:
            with open(file_path, 'r', encoding='iso-8859-1') as file:
                content = file.read()
            
            return self.parse_ldt_content(content)
        except Exception as e:
            self.errors.append(f"Error reading file: {str(e)}")
            return {}
    
    def parse_ldt_content(self, content: str) -> Dict:
        """Parse LDT content string"""
        lines = content.strip().split('\n')
        parsed_data = {
            'patients': [],
            'orders': [],
            'results': [],
            'comments': [],
            'metadata': {
                'file_version': 'LDT 3.2.19',
                'processed_at': datetime.now().isoformat(),
                'total_lines': len(lines)
            }
        }
        
        current_patient = None
        current_order = None
        
        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                continue
                
            try:
                record_type = line[:2]
                if record_type not in self.RECORD_TYPES:
                    self.errors.append(f"Line {line_num}: Unknown record type {record_type}")
                    continue
                
                if record_type == '01':  # Patient Data
                    patient_data = self._parse_patient_record(line)
                    current_patient = patient_data
                    parsed_data['patients'].append(patient_data)
                    
                elif record_type == '02':  # Order Data
                    order_data = self._parse_order_record(line)
                    order_data['patient_id'] = current_patient['id'] if current_patient else None
                    current_order = order_data
                    parsed_data['orders'].append(order_data)
                    
                elif record_type == '03':  # Result Data
                    result_data = self._parse_result_record(line)
                    result_data['order_id'] = current_order['id'] if current_order else None
                    result_data['patient_id'] = current_patient['id'] if current_patient else None
                    parsed_data['results'].append(result_data)
                    
                elif record_type == '04':  # Comment Data
                    comment_data = self._parse_comment_record(line)
                    comment_data['order_id'] = current_order['id'] if current_order else None
                    comment_data['patient_id'] = current_patient['id'] if current_patient else None
                    parsed_data['comments'].append(comment_data)
                    
                elif record_type == '05':  # End of Order
                    if current_order:
                        current_order['end_time'] = datetime.now().isoformat()
                        current_order = None
                        
                elif record_type == '06':  # End of Patient
                    if current_patient:
                        current_patient['end_time'] = datetime.now().isoformat()
                        current_patient = None
                        
            except Exception as e:
                self.errors.append(f"Line {line_num}: Error parsing line: {str(e)}")
        
        parsed_data['errors'] = self.errors
        return parsed_data
    
    def _parse_patient_record(self, line: str) -> Dict:
        """Parse patient record (type 01)"""
        return {
            'id': line[2:12].strip(),
            'last_name': line[12:42].strip(),
            'first_name': line[42:62].strip(),
            'birth_date': self._parse_date(line[62:70]),
            'gender': line[70:71],
            'insurance_number': line[71:81].strip(),
            'insurance_type': line[81:82],
            'record_type': '01'
        }
    
    def _parse_order_record(self, line: str) -> Dict:
        """Parse order record (type 02)"""
        return {
            'id': line[2:12].strip(),
            'order_date': self._parse_date(line[12:20]),
            'order_time': self._parse_time(line[20:26]),
            'ordering_physician': line[26:66].strip(),
            'laboratory': line[66:106].strip(),
            'record_type': '02'
        }
    
    def _parse_result_record(self, line: str) -> Dict:
        """Parse result record (type 03)"""
        return {
            'id': line[2:12].strip(),
            'test_code': line[12:22].strip(),
            'test_name': line[22:82].strip(),
            'result_value': line[82:122].strip(),
            'unit': line[122:132].strip(),
            'reference_range': line[132:172].strip(),
            'abnormal_flag': line[172:173],
            'result_date': self._parse_date(line[173:181]),
            'result_time': self._parse_time(line[181:187]),
            'record_type': '03'
        }
    
    def _parse_comment_record(self, line: str) -> Dict:
        """Parse comment record (type 04)"""
        return {
            'id': line[2:12].strip(),
            'comment_text': line[12:172].strip(),
            'comment_date': self._parse_date(line[172:180]),
            'comment_time': self._parse_time(line[180:186]),
            'record_type': '04'
        }
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date in DDMMYYYY format"""
        if not date_str or date_str.strip() == '00000000':
            return None
        try:
            date_obj = datetime.strptime(date_str.strip(), '%d%m%Y')
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            return None
    
    def _parse_time(self, time_str: str) -> Optional[str]:
        """Parse time in HHMMSS format"""
        if not time_str or time_str.strip() == '000000':
            return None
        try:
            time_obj = datetime.strptime(time_str.strip(), '%H%M%S')
            return time_obj.strftime('%H:%M:%S')
        except ValueError:
            return None
    
    def validate_ldt_file(self, parsed_data: Dict) -> List[str]:
        """Validate parsed LDT data according to KBV specifications"""
        validation_errors = []
        
        # Check required record types
        if not parsed_data['patients']:
            validation_errors.append("No patient records found")
        
        if not parsed_data['orders']:
            validation_errors.append("No order records found")
        
        if not parsed_data['results']:
            validation_errors.append("No result records found")
        
        # Validate patient data
        for patient in parsed_data['patients']:
            if not patient['id']:
                validation_errors.append(f"Patient missing ID")
            if not patient['last_name']:
                validation_errors.append(f"Patient {patient['id']} missing last name")
            if not patient['birth_date']:
                validation_errors.append(f"Patient {patient['id']} missing birth date")
        
        # Validate order data
        for order in parsed_data['orders']:
            if not order['id']:
                validation_errors.append("Order missing ID")
            if not order['patient_id']:
                validation_errors.append(f"Order {order['id']} not linked to patient")
        
        # Validate result data
        for result in parsed_data['results']:
            if not result['test_code']:
                validation_errors.append(f"Result {result['id']} missing test code")
            if not result['order_id']:
                validation_errors.append(f"Result {result['id']} not linked to order")
        
        return validation_errors
    
    def export_to_json(self, parsed_data: Dict) -> str:
        """Export parsed data to JSON format"""
        import json
        
        # Remove datetime objects for JSON serialization
        export_data = parsed_data.copy()
        export_data['metadata']['processed_at'] = str(export_data['metadata']['processed_at'])
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def get_statistics(self, parsed_data: Dict) -> Dict:
        """Get statistics about the parsed LDT file"""
        return {
            'total_patients': len(parsed_data['patients']),
            'total_orders': len(parsed_data['orders']),
            'total_results': len(parsed_data['results']),
            'total_comments': len(parsed_data['comments']),
            'total_errors': len(parsed_data.get('errors', [])),
            'file_size_lines': parsed_data['metadata']['total_lines']
        }