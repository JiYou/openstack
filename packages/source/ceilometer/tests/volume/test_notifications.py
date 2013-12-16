from ceilometer.volume import notifications
from ceilometer.tests import base

NOTIFICATION_VOLUME_EXISTS = {
    u'_context_roles': [u'admin'],
    u'_context_request_id': u'req-7ef29a5d-adeb-48a8-b104-59c05361aa27',
    u'_context_quota_class': None,
    u'event_type': u'volume.exists',
    u'timestamp': u'2012-09-21 09:29:10.620731',
    u'message_id': u'e0e6a5ad-2fc9-453c-b3fb-03fe504538dc',
    u'_context_auth_token': None,
    u'_context_is_admin': True,
    u'_context_project_id': None,
    u'_context_timestamp': u'2012-09-21T09:29:10.266928',
    u'_context_read_deleted': u'no',
    u'_context_user_id': None,
    u'_context_remote_address': None,
    u'publisher_id': u'volume.ubuntu-VirtualBox',
    u'payload': {u'status': u'available',
                 u'audit_period_beginning': u'2012-09-20 00:00:00',
                 u'display_name': u'volume1',
                 u'tenant_id': u'6c97f1ecf17047eab696786d56a0bff5',
                 u'created_at': u'2012-09-20 15:05:16',
                 u'snapshot_id': None,
                 u'volume_type': None,
                 u'volume_id': u'84c363b9-9854-48dc-b949-fe04263f4cf0',
                 u'audit_period_ending': u'2012-09-21 00:00:00',
                 u'user_id': u'4d2fa4b76a4a4ecab8c468c8dea42f89',
                 u'launched_at': u'2012-09-20 15:05:23',
                 u'size': 2},
    u'priority': u'INFO'
}


NOTIFICATION_VOLUME_DELETE = {
    u'_context_roles': [u'Member', u'admin'],
    u'_context_request_id': u'req-6ba8ccb4-1093-4a39-b029-adfaa3fc7ceb',
    u'_context_quota_class': None,
    u'event_type': u'volume.delete.start',
    u'timestamp': u'2012-09-21 10:24:13.168630',
    u'message_id': u'f6e6bc1f-fcd5-41e1-9a86-da7d024f03d9',
    u'_context_auth_token': u'277c6899de8a4b3d999f3e2e4c0915ff',
    u'_context_is_admin': True,
    u'_context_project_id': u'6c97f1ecf17047eab696786d56a0bff5',
    u'_context_timestamp': u'2012-09-21T10:23:54.741228',
    u'_context_read_deleted': u'no',
    u'_context_user_id': u'4d2fa4b76a4a4ecab8c468c8dea42f89',
    u'_context_remote_address': u'192.168.22.101',
    u'publisher_id': u'volume.ubuntu-VirtualBox',
    u'payload': {u'status': u'deleting',
                 u'volume_type_id': None,
                 u'display_name': u'abc',
                 u'tenant_id': u'6c97f1ecf17047eab696786d56a0bff5',
                 u'created_at': u'2012-09-21 10:10:47',
                 u'snapshot_id': None,
                 u'volume_id': u'3b761164-84b4-4eb3-8fcb-1974c641d6ef',
                 u'user_id': u'4d2fa4b76a4a4ecab8c468c8dea42f89',
                 u'launched_at': u'2012-09-21 10:10:50',
                 u'size': 3},
    u'priority': u'INFO'}


class TestNotifications(base.TestCase):

    def _verify_common_counter(self, c, name, notification):
        self.assertFalse(c is None)
        self.assertEqual(c.name, name)
        self.assertEqual(c.resource_id, notification['payload']['volume_id'])
        self.assertEqual(c.timestamp, notification['timestamp'])
        metadata = c.resource_metadata
        self.assertEquals(metadata.get('host'), notification['publisher_id'])

    def test_volume_exists(self):
        v = notifications.Volume()
        counters = v.process_notification(NOTIFICATION_VOLUME_EXISTS)
        self.assertEqual(len(counters), 1)
        c = counters[0]
        self._verify_common_counter(c, 'volume', NOTIFICATION_VOLUME_EXISTS)
        self.assertEqual(c.volume, 1)

    def test_volume_size_exists(self):
        v = notifications.VolumeSize()
        counters = v.process_notification(NOTIFICATION_VOLUME_EXISTS)
        self.assertEqual(len(counters), 1)
        c = counters[0]
        self._verify_common_counter(c, 'volume.size',
                                    NOTIFICATION_VOLUME_EXISTS)
        self.assertEqual(c.volume,
                         NOTIFICATION_VOLUME_EXISTS['payload']['size'])

    def test_volume_delete(self):
        v = notifications.Volume()
        counters = v.process_notification(NOTIFICATION_VOLUME_DELETE)
        self.assertEqual(len(counters), 1)
        c = counters[0]
        self._verify_common_counter(c, 'volume', NOTIFICATION_VOLUME_DELETE)
        self.assertEqual(c.volume, 1)

    def test_volume_size_delete(self):
        v = notifications.VolumeSize()
        counters = v.process_notification(NOTIFICATION_VOLUME_DELETE)
        self.assertEqual(len(counters), 1)
        c = counters[0]
        self._verify_common_counter(c, 'volume.size',
                                    NOTIFICATION_VOLUME_DELETE)
        self.assertEqual(c.volume,
                         NOTIFICATION_VOLUME_DELETE['payload']['size'])
