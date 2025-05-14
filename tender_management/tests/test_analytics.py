from odoo.tests.common import TransactionCase, tagged
from unittest.mock import patch
import json


@tagged('post_install', '-at_install')
class TestAnalytics(TransactionCase):
    
    def setUp(self):
        super(TestAnalytics, self).setUp()
        
        # Create tender types
        self.type_construction = self.env['tender.type'].create({
            'name': 'Construction',
            'code': 'CONST',
        })
        
        self.type_services = self.env['tender.type'].create({
            'name': 'Services',
            'code': 'SRV',
        })
        
        self.type_goods = self.env['tender.type'].create({
            'name': 'Goods',
            'code': 'GDS',
        })
        
        # Create tenders
        # Construction tenders
        for i in range(5):
            self.env['tender.tender'].create({
                'name': f'Construction Tender {i+1}',
                'reference': f'CONST-2024-{i+1:03d}',
                'tender_type_id': self.type_construction.id,
                'submission_deadline': '2024-12-31 23:59:59',
                'estimated_value': 100000.00 + (i * 10000),
                'currency_id': self.env.ref('base.USD').id,
                'state': 'published' if i < 3 else 'draft',
            })
        
        # Services tenders
        for i in range(3):
            self.env['tender.tender'].create({
                'name': f'Service Tender {i+1}',
                'reference': f'SRV-2024-{i+1:03d}',
                'tender_type_id': self.type_services.id,
                'submission_deadline': '2024-11-30 23:59:59',
                'estimated_value': 50000.00 + (i * 5000),
                'currency_id': self.env.ref('base.USD').id,
                'state': 'closed' if i < 2 else 'awarded',
            })
        
        # Goods tenders
        for i in range(2):
            self.env['tender.tender'].create({
                'name': f'Goods Tender {i+1}',
                'reference': f'GDS-2024-{i+1:03d}',
                'tender_type_id': self.type_goods.id,
                'submission_deadline': '2024-10-31 23:59:59',
                'estimated_value': 25000.00 + (i * 2500),
                'currency_id': self.env.ref('base.USD').id,
                'state': 'awarded',
            })
    
    def test_tender_count_by_type(self):
        """Test tender count by type analytics"""
        analytics = self.env['tender.analytics'].create({})
        results = analytics.get_tender_count_by_type()
        
        # Verify count by type
        self.assertEqual(results['Construction'], 5, "Wrong count for Construction tenders")
        self.assertEqual(results['Services'], 3, "Wrong count for Services tenders")
        self.assertEqual(results['Goods'], 2, "Wrong count for Goods tenders")
    
    def test_tender_value_by_state(self):
        """Test tender value by state analytics"""
        analytics = self.env['tender.analytics'].create({})
        results = analytics.get_tender_value_by_state()
        
        # Calculate expected values
        draft_value = sum([100000.00 + (i * 10000) for i in range(3, 5)])
        published_value = sum([100000.00 + (i * 10000) for i in range(3)])
        closed_value = sum([50000.00 + (i * 5000) for i in range(2)])
        awarded_value = 50000.00 + (2 * 5000) + sum([25000.00 + (i * 2500) for i in range(2)])
        
        # Verify values by state
        self.assertAlmostEqual(results['draft'], draft_value, delta=0.01, msg="Wrong value for draft tenders")
        self.assertAlmostEqual(results['published'], published_value, delta=0.01, msg="Wrong value for published tenders")
        self.assertAlmostEqual(results['closed'], closed_value, delta=0.01, msg="Wrong value for closed tenders")
        self.assertAlmostEqual(results['awarded'], awarded_value, delta=0.01, msg="Wrong value for awarded tenders")
    
    @patch('odoo.addons.tender_management.external.ai_service.ai_analyzer.AIAnalyzer.predict_success_rate')
    def test_success_prediction(self, mock_predict_success_rate):
        """Test tender success prediction analytics"""
        # Mock AI prediction response
        mock_predict_success_rate.return_value = {
            'predicted_success_rate': 0.75,
            'confidence': 0.85,
            'factors': {
                'bid_competitiveness': 0.8,
                'technical_alignment': 0.7,
                'past_performance': 0.9,
            }
        }
        
        # Create a bid
        tender = self.env['tender.tender'].search([('tender_type_id', '=', self.type_construction.id)], limit=1)
        bid = self.env['tender.bid'].create({
            'tender_id': tender.id,
            'partner_id': self.env['res.partner'].create({'name': 'Test Bidder'}).id,
            'amount': 95000.00,
            'currency_id': self.env.ref('base.USD').id,
            'technical_score': 85,
        })
        
        # Predict success
        analytics = self.env['tender.analytics'].create({})
        result = analytics.predict_bid_success(bid.id)
        
        # Verify prediction result
        self.assertEqual(result['predicted_success_rate'], 0.75, "Wrong predicted success rate")
        self.assertEqual(result['confidence'], 0.85, "Wrong prediction confidence")
        
    def test_dashboards_data_generation(self):
        """Test dashboard data generation"""
        # Create dashboard
        dashboard = self.env['tender.dashboard'].create({
            'name': 'Test Dashboard',
            'user_id': self.env.user.id,
        })
        
        # Generate dashboard data
        dashboard.action_generate_data()
        
        # Verify dashboard data was generated
        self.assertTrue(dashboard.data, "Dashboard data not generated")
        
        # Parse data and check content
        data = json.loads(dashboard.data)
        self.assertIn('tender_count', data, "Missing tender count in dashboard data")
        self.assertIn('tender_value', data, "Missing tender value in dashboard data")
        self.assertIn('tender_by_state', data, "Missing tender by state in dashboard data")
        
        # Check total tender count
        self.assertEqual(data['tender_count'], 10, "Wrong total tender count in dashboard")
