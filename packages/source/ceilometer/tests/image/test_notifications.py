# -*- encoding: utf-8 -*-
#
# Copyright © 2012 Red Hat Inc.
#
# Author: Eoghan Glynn <eglynn@redhat.com>
# Author: Julien danjou <julien@danjou.info>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from datetime import datetime

from ceilometer.image import notifications
from ceilometer import counter
from ceilometer.tests import base


def fake_uuid(x):
    return '%s-%s-%s-%s' % (x * 8, x * 4, x * 4, x * 12)


NOW = datetime.isoformat(datetime.utcnow())

NOTIFICATION_SEND = {
    u'event_type': u'image.send',
    u'timestamp': NOW,
    u'message_id': fake_uuid('a'),
    u'priority': u'INFO',
    u'publisher_id': u'images.example.com',
    u'payload': {u'receiver_tenant_id': fake_uuid('b'),
                 u'destination_ip': u'1.2.3.4',
                 u'bytes_sent': 42,
                 u'image_id': fake_uuid('c'),
                 u'receiver_user_id': fake_uuid('d'),
                 u'owner_id': fake_uuid('e')}
}

IMAGE_META = {u'status': u'saving',
              u'name': u'fake image #3',
              u'deleted': False,
              u'container_format': u'ovf',
              u'created_at': u'2012-09-18T10:13:44.571370',
              u'disk_format': u'vhd',
              u'updated_at': u'2012-09-18T10:13:44.623120',
              u'properties': {u'key2': u'value2',
                              u'key1': u'value1'},
              u'min_disk': 0,
              u'protected': False,
              u'id': fake_uuid('c'),
              u'location': None,
              u'checksum': u'd990432ef91afef3ad9dbf4a975d3365',
              u'owner': "fake",
              u'is_public': False,
              u'deleted_at': None,
              u'min_ram': 0,
              u'size': 19}


NOTIFICATION_UPDATE = {"message_id": "0c65cb9c-018c-11e2-bc91-5453ed1bbb5f",
                       "publisher_id": "images.example.com",
                       "event_type": "image.update",
                       "priority": "info",
                       "payload": IMAGE_META,
                       "timestamp": NOW}


NOTIFICATION_UPLOAD = {"message_id": "0c65cb9c-018c-11e2-bc91-5453ed1bbb5f",
                       "publisher_id": "images.example.com",
                       "event_type": "image.upload",
                       "priority": "info",
                       "payload": IMAGE_META,
                       "timestamp": NOW}


NOTIFICATION_DELETE = {"message_id": "0c65cb9c-018c-11e2-bc91-5453ed1bbb5f",
                       "publisher_id": "images.example.com",
                       "event_type": "image.delete",
                       "priority": "info",
                       "payload": IMAGE_META,
                       "timestamp": NOW}


class TestNotification(base.TestCase):

    def _verify_common_counter(self, c, name, volume):
        self.assertFalse(c is None)
        self.assertEqual(c.name, name)
        self.assertEqual(c.resource_id, fake_uuid('c'))
        self.assertEqual(c.timestamp, NOW)
        self.assertEqual(c.volume, volume)
        metadata = c.resource_metadata
        self.assertEquals(metadata.get('host'), u'images.example.com')

    def test_image_download(self):
        handler = notifications.ImageDownload()
        counters = handler.process_notification(NOTIFICATION_SEND)
        self.assertEqual(len(counters), 1)
        download = counters[0]
        self._verify_common_counter(download, 'image.download', 42)
        self.assertEqual(download.user_id, fake_uuid('d'))
        self.assertEqual(download.project_id, fake_uuid('b'))
        self.assertEqual(download.type, counter.TYPE_DELTA)

    def test_image_serve(self):
        handler = notifications.ImageServe()
        counters = handler.process_notification(NOTIFICATION_SEND)
        self.assertEqual(len(counters), 1)
        serve = counters[0]
        self._verify_common_counter(serve, 'image.serve', 42)
        self.assertEqual(serve.project_id, fake_uuid('e'))
        self.assertEquals(serve.resource_metadata.get('receiver_user_id'),
                          fake_uuid('d'))
        self.assertEquals(serve.resource_metadata.get('receiver_tenant_id'),
                          fake_uuid('b'))
        self.assertEqual(serve.type, counter.TYPE_DELTA)

    def test_image_crud_on_update(self):
        handler = notifications.ImageCRUD()
        counters = handler.process_notification(NOTIFICATION_UPDATE)
        self.assertEqual(len(counters), 1)
        update = counters[0]
        self._verify_common_counter(update, 'image.update', 1)
        self.assertEqual(update.type, counter.TYPE_DELTA)

    def test_image_on_update(self):
        handler = notifications.Image()
        counters = handler.process_notification(NOTIFICATION_UPDATE)
        self.assertEqual(len(counters), 1)
        update = counters[0]
        self._verify_common_counter(update, 'image', 1)
        self.assertEqual(update.type, counter.TYPE_GAUGE)

    def test_image_size_on_update(self):
        handler = notifications.ImageSize()
        counters = handler.process_notification(NOTIFICATION_UPDATE)
        self.assertEqual(len(counters), 1)
        update = counters[0]
        self._verify_common_counter(update, 'image.size',
                                    IMAGE_META['size'])
        self.assertEqual(update.type, counter.TYPE_GAUGE)

    def test_image_crud_on_upload(self):
        handler = notifications.ImageCRUD()
        counters = handler.process_notification(NOTIFICATION_UPLOAD)
        self.assertEqual(len(counters), 1)
        upload = counters[0]
        self._verify_common_counter(upload, 'image.upload', 1)
        self.assertEqual(upload.type, counter.TYPE_DELTA)

    def test_image_on_upload(self):
        handler = notifications.Image()
        counters = handler.process_notification(NOTIFICATION_UPLOAD)
        self.assertEqual(len(counters), 1)
        upload = counters[0]
        self._verify_common_counter(upload, 'image', 1)
        self.assertEqual(upload.type, counter.TYPE_GAUGE)

    def test_image_size_on_upload(self):
        handler = notifications.ImageSize()
        counters = handler.process_notification(NOTIFICATION_UPLOAD)
        self.assertEqual(len(counters), 1)
        upload = counters[0]
        self._verify_common_counter(upload, 'image.size',
                                    IMAGE_META['size'])
        self.assertEqual(upload.type, counter.TYPE_GAUGE)

    def test_image_crud_on_delete(self):
        handler = notifications.ImageCRUD()
        counters = handler.process_notification(NOTIFICATION_DELETE)
        self.assertEqual(len(counters), 1)
        delete = counters[0]
        self._verify_common_counter(delete, 'image.delete', 1)
        self.assertEqual(delete.type, counter.TYPE_DELTA)

    def test_image_on_delete(self):
        handler = notifications.Image()
        counters = handler.process_notification(NOTIFICATION_DELETE)
        self.assertEqual(len(counters), 1)
        delete = counters[0]
        self._verify_common_counter(delete, 'image', 1)
        self.assertEqual(delete.type, counter.TYPE_GAUGE)

    def test_image_size_on_delete(self):
        handler = notifications.ImageSize()
        counters = handler.process_notification(NOTIFICATION_DELETE)
        self.assertEqual(len(counters), 1)
        delete = counters[0]
        self._verify_common_counter(delete, 'image.size',
                                    IMAGE_META['size'])
        self.assertEqual(delete.type, counter.TYPE_GAUGE)
