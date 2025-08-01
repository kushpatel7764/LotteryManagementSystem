import unittest
from unittest.mock import patch, MagicMock
from src.app import app

class ScanTicketsRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.db_path = "dummy_path"

    @patch('app.DatabaseQueries.get_scan_ticket_page_table')
    @patch('app.calculate_instant_tickets_sold')
    @patch('app.DatabaseQueries.count_activated_books')
    @patch('app.load_config')
    def test_scan_tickets_get(self, mock_config, mock_count_books, mock_sold_total, mock_scan_table):
        # Mock return values
        mock_scan_table.return_value = []
        mock_sold_total.return_value = 0
        mock_config.return_value = {'ticket_order': 'descending'}
        mock_count_books.return_value = 0

        response = self.client.get('/scan_tickets')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'"message_type": ""', response.data)

    @patch('app.ScannedCodeManagement')
    @patch('app.DatabaseQueries.get_all_active_book_ids')
    @patch('app.DatabaseQueries.get_scan_ticket_page_table')
    @patch('app.calculate_instant_tickets_sold')
    @patch('app.DatabaseQueries.count_activated_books')
    @patch('app.load_config')
    def test_invalid_barcode(self, mock_config, mock_count_books, mock_sold_total, mock_scan_table,
                             mock_active_books, mock_scanned_manager):
        mock_active_books.return_value = ['B001']
        mock_instance = MagicMock()
        mock_instance.extract_all_scanned_code.return_value = "INVALID BARCODE"
        mock_scanned_manager.return_value = mock_instance
        mock_scan_table.return_value = []
        mock_sold_total.return_value = 0
        mock_config.return_value = {'ticket_order': 'descending'}
        mock_count_books.return_value = 0

        response = self.client.post('/scan_tickets', data={'scanned_code': 'dummy_invalid'})
        self.assertIn(b'"message": "INVALID BARCODE"', response.data)

    @patch('app.ScannedCodeManagement')
    @patch('app.DatabaseQueries.get_all_active_book_ids')
    @patch('app.DatabaseQueries.get_scan_ticket_page_table')
    @patch('app.calculate_instant_tickets_sold')
    @patch('app.DatabaseQueries.count_activated_books')
    @patch('app.load_config')
    def test_unactivated_book(self, mock_config, mock_count_books, mock_sold_total, mock_scan_table,
                              mock_active_books, mock_scanned_manager):
        mock_active_books.return_value = ['B002']  # Book in scanned_info not active
        mock_instance = MagicMock()
        mock_instance.extract_all_scanned_code.return_value = {
            "book_id": "B001",
            "game_number": "G123",
            "ticket_number": 10,
            "ticket_price": 5
        }
        mock_scanned_manager.return_value = mock_instance
        mock_scan_table.return_value = []
        mock_sold_total.return_value = 0
        mock_config.return_value = {'ticket_order': 'descending'}
        mock_count_books.return_value = 0

        response = self.client.post('/scan_tickets', data={'scanned_code': 'valid_code'})
        self.assertIn(b"Book IS NOT ACTIVATED", response.data)

    @patch('app.add_sales_log')
    @patch('app.Database.update_counting_ticket_number')
    @patch('app.insert_ticket')
    @patch('app.DatabaseQueries.get_ticket_name')
    @patch('app.ScannedCodeManagement')
    @patch('app.DatabaseQueries.get_all_active_book_ids')
    @patch('app.DatabaseQueries.get_scan_ticket_page_table')
    @patch('app.calculate_instant_tickets_sold')
    @patch('app.DatabaseQueries.count_activated_books')
    @patch('app.load_config')
    def test_valid_ticket_scan(self, mock_config, mock_count_books, mock_sold_total, mock_scan_table,
                               mock_active_books, mock_scanned_manager, mock_get_name, mock_insert_ticket,
                               mock_update_count, mock_add_log):
        mock_active_books.return_value = ['B001']
        mock_instance = MagicMock()
        mock_instance.extract_all_scanned_code.return_value = {
            "book_id": "B001",
            "game_number": "G123",
            "ticket_number": 42,
            "ticket_price": 10
        }
        mock_scanned_manager.return_value = mock_instance
        mock_get_name.return_value = "Super Cash"
        mock_insert_ticket.return_value = None
        mock_update_count.return_value = None
        mock_add_log.return_value = None
        mock_scan_table.return_value = []
        mock_sold_total.return_value = 0
        mock_config.return_value = {'ticket_order': 'descending'}
        mock_count_books.return_value = 0

        response = self.client.post('/scan_tickets', data={'scanned_code': 'valid_code'})
        self.assertIn(b"TICKET SCANNED", response.data)

if __name__ == '__main__':
    unittest.main()
