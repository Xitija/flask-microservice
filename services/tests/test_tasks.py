import unittest
import json
import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.tasks import app

class TestTaskAPI(unittest.TestCase):
    def setUp(self):
        """Set up test client and test data"""
        self.app = app.test_client()
        self.app.testing = True
        self.base_url = '/api/tasks'
        
        # Test task data
        self.test_task = {
            'title': 'Test Task',
            'description': 'This is a test task'
        }
        
        # Create a task for update and delete tests
        response = self.app.post(
            self.base_url,
            data=json.dumps(self.test_task),
            content_type='application/json'
        )
        self.task_id = json.loads(response.data)['data']['id']

    def tearDown(self):
        """Clean up after tests"""
        # Delete the test task if it exists
        if hasattr(self, 'task_id'):
            self.app.delete(f'{self.base_url}/{self.task_id}')

    def test_create_task(self):
        """Test creating a new task"""
        # Test valid task creation
        response = self.app.post(
            self.base_url,
            data=json.dumps(self.test_task),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['data']['title'], self.test_task['title'])
        self.assertEqual(data['data']['description'], self.test_task['description'])
        self.assertEqual(data['data']['status'], 'pending')

        # Test missing required fields
        response = self.app.post(
            self.base_url,
            data=json.dumps({'title': 'Missing Description'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

        # Test invalid data types
        response = self.app.post(
            self.base_url,
            data=json.dumps({'title': 123, 'description': 'Test'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_get_tasks(self):
        """Test getting tasks with pagination"""
        # Test default pagination
        response = self.app.get(self.base_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('data', data)
        self.assertIn('pagination', data)

        # Test custom pagination
        response = self.app.get(f'{self.base_url}?page=1&per_page=5')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['pagination']['per_page'], 5)

        # Test invalid pagination parameters
        response = self.app.get(f'{self.base_url}?page=0&per_page=10')
        self.assertEqual(response.status_code, 400)

    def test_update_task(self):
        """Test updating a task"""
        update_data = {
            'title': 'Updated Title',
            'description': 'Updated Description',
            'status': 'in_progress'
        }

        # Test valid update
        response = self.app.put(
            f'{self.base_url}/{self.task_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['data']['title'], update_data['title'])
        self.assertEqual(data['data']['description'], update_data['description'])
        self.assertEqual(data['data']['status'], update_data['status'])

        # Test update non-existent task
        response = self.app.put(
            f'{self.base_url}/999999',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

        # Test invalid status
        response = self.app.put(
            f'{self.base_url}/{self.task_id}',
            data=json.dumps({'status': 'invalid_status'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_delete_task(self):
        """Test deleting a task"""
        # Test valid deletion
        response = self.app.delete(f'{self.base_url}/{self.task_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')

        # Test delete non-existent task
        response = self.app.delete(f'{self.base_url}/999999')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main() 