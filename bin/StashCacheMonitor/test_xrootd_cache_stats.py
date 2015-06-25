#!/usr/bin/python

import unittest
import os
import mock
import xrootd_cache_stats
import cStringIO

good_cinfo_file = ('\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\t\x00\x00\x00\xff\x01\x03\x00\x00\x00\xa7\xf3\x1eU'
'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00m\xad\x81\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xb2\xf3\x1eU'
'\x00\x00\x00\x00m\xad\x81\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x8c\x16fU'
'\x00\x00\x00\x00m\xad\x81\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

def mockXRootDServer():
    import XRootD.client
    XRootDFSMock = mock.Mock(spec=XRootD.client.FileSystem)
    result = mock.Mock()
    result.configure_mock(ok=True,error=False,fatal=False, message='[SUCCESS]', code=0)
    XRootDFSMock.return_value.ping.return_value = (result, None)
    return XRootDFSMock

def mockFileSystem():

    FSMock = mock.NonCallableMock()
    return FSMock

class TestStatsCollection(unittest.TestCase):

    def test_xrood_server(self):

        XRootDFSMock = mockXRootDServer()
        with mock.patch('XRootD.client.FileSystem', XRootDFSMock):
            url = 'xroot://dummy'
            cadd = xrootd_cache_stats.test_xrootd_server(url)
            XRootDFSMock.assert_called_with(url)
            assert XRootDFSMock.return_value.ping.called
            assert cadd['ping_response_status'] == 'ok'
            assert cadd['ping_elapsed_time'] > 0

    def test_read_cinfo_file(self):

        mock_open = mock.MagicMock(spec=file)
        mock_open.return_value = cStringIO.StringIO(good_cinfo_file)
        with mock.patch.object(xrootd_cache_stats, 'open' , mock_open, create=True):
            result = xrootd_cache_stats.read_cinfo('x.cinfo', 1432763080)
        self.assertEqual(result, {'naccesses': 3, 'last_access': 1432753804, 'by_hour': {'24': 1, '12': 1, '01': 0}})

        # empty input
        mock_open = mock.MagicMock(spec=file)
        mock_open.return_value = cStringIO.StringIO('')
        with mock.patch.object(xrootd_cache_stats, 'open' , mock_open, create=True):
            self.assertRaises(xrootd_cache_stats.ReadCInfoError, xrootd_cache_stats.read_cinfo, 'x.cinfo', 1432763080)

        # mangled input
        mock_open = mock.MagicMock(spec=file)
        mock_open.return_value = cStringIO.StringIO(good_cinfo_file[:-1])
        with mock.patch.object(xrootd_cache_stats, 'open' , mock_open, create=True):
            try:
                result = xrootd_cache_stats.read_cinfo('x.cinfo', 1432763080)
            except xrootd_cache_stats.ReadCInfoError, ex:
                result = ex.access_info
        self.assertEqual(result, {'naccesses': 3, 'last_access': 0, 'by_hour': {'24': 0, '12': 0, '01': 0}})

    def test_scan_vo_dir(self):

        osstat = mock.Mock(return_value=mock.Mock(st_blocks=256))
        oswalk = mock.Mock(side_effect=( (('a', [], ['x','y', 'x.cinfo', 'y.cinfo']),), (('b', [], []),)))
        read_cinfo = mock.Mock(return_value= { 'naccesses': 1, 'last_access': 1432753804, 'by_hour': {'24': 2, '12': 1, '01': 0}})
        with mock.patch('xrootd_cache_stats.read_cinfo', read_cinfo):
            with mock.patch.multiple('os', walk=oswalk, stat=osstat):
                cadd = xrootd_cache_stats.scan_vo_dir('a')
        assert cadd['nfiles'] == 2

    def test_scan_cache_dirs(self):

        # it might be simpler to just create some real files instead of faking all this
        oslistdir = mock.Mock(side_effect=(['a','b','c'], ['x','y', 'x.cinfo', 'y.cinfo'], ['z','z.cinfo','zz']))
        ospathisdir = mock.Mock(side_effect=lambda path: os.path.basename(path) in ['a','b','c','d'])
        osstat = mock.Mock(return_value=mock.Mock(st_blocks=256))

        import classad
        scan_vo_dir = mock.Mock(return_value=classad.ClassAd("""
    [
        bytes_hr_24 = 524288;
        naccesses_hr_01 = 0;
        most_recent_access_time = 1432753804;
        used_bytes = 262144;
        naccesses_hr_24 = 4;
        bytes_hr_12 = 262144;
        nfiles = 2;
        naccesses = 2;
        bad_cinfo_files = 0;
        naccesses_hr_12 = 2;
        bytes_hr_01 = 0
    ]
    """))

        with mock.patch('xrootd_cache_stats.scan_vo_dir', scan_vo_dir):
            with mock.patch.multiple('os', listdir=oslistdir, stat=osstat):
                with mock.patch('os.path.isdir', ospathisdir):
                    result = xrootd_cache_stats.scan_cache_dirs('/foo')
        assert result['a']['nfiles'] == 2
        assert result['a']['used_bytes'] == 262144
        assert result['b']['nfiles'] == 2
        assert result['b']['used_bytes'] == 262144
        assert result['c']['nfiles'] == 2
        assert result['c']['used_bytes'] == 262144

    def test_get_cache_info(self):

        osstatvfs = mock.Mock(return_value=mock.Mock(f_blocks=262144, f_bsize=4096, f_bfree=32768))
        with mock.patch('os.statvfs', osstatvfs):
            cadd = xrootd_cache_stats.get_cache_info('/dummy', 0.9)
            assert cadd['total_cache_bytes'] == int(1073741824 * 0.9)
            assert cadd['free_cache_bytes'] == 26843545
            self.assertEqual(cadd['free_cache_fraction'], 0.02777530528252148)

    def test_collect_cache_stats(self):

        import classad

        mock_scan_cache_dirs = mock.Mock(return_value=classad.ClassAd({}))
        mock_test_xrootd_server = mock.Mock(return_value=classad.ClassAd({}))
        mock_get_cache_info = mock.Mock(return_value=classad.ClassAd({}))
        with mock.patch.multiple(
                xrootd_cache_stats,
                scan_cache_dirs=mock_scan_cache_dirs,
                test_xrootd_server=mock_test_xrootd_server,
                get_cache_info = mock_get_cache_info
                ):
            cadd = xrootd_cache_stats.collect_cache_stats('xroot://dummy', '/dummy', 1.0)
        mock_scan_cache_dirs.assert_called('/dummy')
        mock_test_xrootd_server.assert_called('xroot://dummy')
        mock_get_cache_info.assert_called('/dummy', 1.0)

if __name__ == '__main__':
    unittest.main()

