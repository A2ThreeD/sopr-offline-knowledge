# SOPR Offline Knowledge
# Copyright (c) 2026 Aaron Morris / A2ThreeD.
# Regression checks for catalog discovery and asynchronous refresh.
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location('portal', Path(__file__).resolve().parents[1] / 'app/sopr_portal.py')
portal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(portal)

class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = portal.PortalState.__new__(portal.PortalState)
        self.state.content_catalog_cache_file = Path(self.tmp.name) / 'cache.json'
        self.state.content_catalog_lock = threading.Lock()
        self.state.content_catalog_refresh_thread = None
        self.state.content_catalog_refresh_error = None
        self.state.content_catalog_refresh_attempt = 0
        self.state.maps_env = lambda: {}
        self.state.list_installed_zims = lambda: []
        self.state.read_custom_zim_selection = lambda: {}

    def cache(self, items, age=0):
        self.state.content_catalog_cache_file.write_text(json.dumps({'fetched_at': time.time()-age, 'payload': {'items': items, 'source': {'root_url': self.state.zim_catalog_root()}}}))

    def test_direct_root_index(self):
        with patch.object(portal.request, 'urlopen', return_value=io.BytesIO(b'<a href="other/">other/</a>')) as fetch:
            links = self.state.fetch_directory_listing(self.state.zim_catalog_root())
        self.assertEqual(fetch.call_args.args[0].full_url, portal.KIWIX_MIRROR_ROOT)
        self.assertEqual(links[0]['href'], 'other/')

    def test_dotsrc_span_links_and_binary_sizes(self):
        parser = portal.DirectoryIndexParser()
        parser.feed(
            '<tr><td><span href="gutenberg/">gutenberg/</span></td><td>-</td></tr>'
            '<tr><td><span href="book.zim">book.zim</span></td><td>1.5 MiB</td></tr>'
        )
        self.assertEqual([item["href"] for item in parser.links], ["gutenberg/", "book.zim"])
        self.assertEqual(parser.links[1]["size_bytes"], 1572864)

    def test_legacy_root_and_cache_move_to_debian(self):
        self.state.maps_env = lambda: {'PREPMASTER_ZIM_CATALOG_URL': 'https://download.kiwix.org/zim/'}
        self.assertEqual(self.state.zim_catalog_root(), portal.KIWIX_MIRROR_ROOT)
        self.state.content_catalog_cache_file.write_text(json.dumps({
            'fetched_at': time.time(),
            'payload': {'source': {'root_url': 'https://download.kiwix.org/zim/'}, 'items': [{'name': 'old.zim'}]},
        }))
        self.assertIsNone(self.state.load_content_catalog_cache())

    def test_rejects_marketing_page_and_preserves_cache(self):
        self.cache([{'name':'saved.zim'}])
        before = self.state.content_catalog_cache_file.read_bytes()
        self.state.fetch_directory_listing = Mock(return_value=[{'href':'https://hub.kiwix.org/downloads/'}])
        with self.assertRaisesRegex(RuntimeError, 'valid category index'):
            self.state.build_kiwix_catalog_payload()
        self.assertEqual(self.state.content_catalog_cache_file.read_bytes(), before)

    def test_only_categories_and_zims_are_indexed(self):
        self.state.fetch_directory_listing = Mock(side_effect=[
            [{'href':'../'}, {'href':'https://example.com/'}, {'href':'other/'}],
            [{'href':'book.zim','size_bytes':123}, {'href':'book.zim.sha256'}]])
        result=self.state.build_kiwix_catalog_payload()
        self.assertEqual(len(result['items']),1)
        self.assertEqual(result['items'][0]['download_url'],portal.KIWIX_MIRROR_ROOT + 'other/book.zim')

    def test_empty_first_load_is_background_and_single_worker(self):
        self.cache([])
        entered=threading.Event(); release=threading.Event()
        def build():
            entered.set(); release.wait(2); self.cache([{'name':'new.zim'}])
        self.state.build_kiwix_catalog_payload = Mock(side_effect=build)
        try:
            first=self.state.fetch_kiwix_catalog_cached()
            self.assertTrue(first['refreshing'])
            self.assertTrue(entered.wait(1))
            worker=self.state.content_catalog_refresh_thread
            self.assertTrue(self.state.fetch_kiwix_catalog_cached()['refreshing'])
            self.assertEqual(self.state.build_kiwix_catalog_payload.call_count,1)
        finally:
            release.set()
            if self.state.content_catalog_refresh_thread:
                self.state.content_catalog_refresh_thread.join(3)
        result=self.state.fetch_kiwix_catalog_cached()
        self.assertFalse(result['refreshing'])
        self.assertEqual(result['items'][0]['name'],'new.zim')

    def test_failed_refresh_is_visible_and_retains_saved_data(self):
        self.cache([{'name':'saved.zim'}],age=7200)
        self.state.build_kiwix_catalog_payload=Mock(side_effect=TimeoutError('catalog timed out'))
        self.state.fetch_kiwix_catalog_cached()
        worker=self.state.content_catalog_refresh_thread
        if worker: worker.join(2)
        result=self.state.fetch_kiwix_catalog_cached()
        self.assertFalse(result['refreshing'])
        self.assertTrue(result['stale'])
        self.assertIn('timed out',result['error'])
        self.assertEqual(result['items'][0]['name'],'saved.zim')
        self.assertEqual(self.state.build_kiwix_catalog_payload.call_count,1)

if __name__ == '__main__':
    unittest.main()
