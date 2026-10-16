"""Small fictional HEIC conversion checks, not real phone-library validation."""
from pathlib import Path
import contextlib
import io
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image
import convert_heic as tool
import make_sample

EXE = os.environ.get('MAGICK_EXE', 'magick')


def state(folder):
    return {p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in folder.iterdir()}


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='heic-tests-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root/'photos'
        with contextlib.redirect_stdout(io.StringIO()):
            make_sample.make(self.source)
        self.out = self.root/'jpgs'

    def convert(self, source=None, destination=None):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            tool.convert(source or self.source, destination or self.out, EXE)
        return out.getvalue()

    def test_conversion_decodes_all_three_expected_sizes(self):
        before = state(self.source)
        report = self.convert()
        self.assertEqual(before, state(self.source))
        self.assertEqual(sorted(p.name for p in self.out.iterdir()), ['sample1.jpg','sample2.jpg','sample3.jpg'])
        for i,size in enumerate([(64,48),(80,60),(48,48)],1):
            with Image.open(self.out/f'sample{i}.jpg') as im:
                im.load()
                self.assertEqual(im.format,'JPEG')
                self.assertEqual(im.size,size)
                self.assertTrue(any(lo != hi for lo,hi in im.getextrema()))
                self.assertEqual(len(im.getexif()),0)
        self.assertIn('SHA256 digests unchanged',report)
        self.assertIn('Lossy JPEG',report)

    def test_repeat_conversion_preserves_all_existing_output_bytes_and_times(self):
        self.convert()
        before = state(self.out),state(self.source)
        with self.assertRaises(FileExistsError):self.convert()
        self.assertEqual(before,(state(self.out),state(self.source)))

    def test_existing_destination_file_preserved(self):
        self.out.write_bytes(b'KEEP')
        with self.assertRaises(FileExistsError):self.convert()
        self.assertEqual(self.out.read_bytes(),b'KEEP')

    def test_existing_unrelated_directory_preserved(self):
        self.out.mkdir();(self.out/'private.txt').write_bytes(b'KEEP')
        before = state(self.out)
        with self.assertRaises(FileExistsError):self.convert()
        self.assertEqual(before,state(self.out))

    def test_repeat_setup_preserves_bytes_and_times(self):
        before=state(self.source)
        with self.assertRaises(FileExistsError):make_sample.make(self.source)
        self.assertEqual(before,state(self.source))

    def test_setup_existing_file_preserved(self):
        target=self.root/'file';target.write_bytes(b'KEEP')
        with self.assertRaises(FileExistsError):make_sample.make(target)
        self.assertEqual(target.read_bytes(),b'KEEP')

    def test_invalid_heic_fails_without_source_changes(self):
        (self.source/'sample1.heic').write_bytes(b'NOT HEIC')
        before=state(self.source)
        with self.assertRaises(OSError):self.convert()
        self.assertEqual(before,state(self.source))
        self.assertFalse((self.out/'sample1.jpg').exists())

    def test_empty_folder_refused_before_output_creation(self):
        empty=self.root/'empty';empty.mkdir()
        with self.assertRaises(OSError):self.convert(empty)
        self.assertFalse(self.out.exists())

    def test_subfolder_refused(self):
        (self.source/'nested').mkdir()
        with self.assertRaises(OSError):self.convert()
        self.assertFalse(self.out.exists())

    def test_non_heic_refused(self):
        (self.source/'notes.txt').write_bytes(b'KEEP')
        with self.assertRaises(OSError):self.convert()
        self.assertFalse(self.out.exists())

    def test_interpretation_characters_refused(self):
        (self.source/'sample1.heic').rename(self.source/'x[0].heic')
        with self.assertRaises(OSError):self.convert()
        self.assertFalse(self.out.exists())

    def test_case_colliding_stems_refused(self):
        (self.source/'sample1.HEIC').write_bytes((self.source/'sample1.heic').read_bytes())
        if len(list(self.source.iterdir())) != 4:
            self.skipTest('Case-distinct filenames unavailable on this filesystem')
        with self.assertRaises(OSError):self.convert()
        self.assertFalse(self.out.exists())

    def test_hardlink_source_refused(self):
        outside=self.root/'keep.heic';shutil.copyfile(self.source/'sample1.heic',outside)
        (self.source/'sample1.heic').unlink();os.link(outside,self.source/'sample1.heic')
        before=outside.read_bytes()
        with self.assertRaises(OSError):self.convert()
        self.assertEqual(before,outside.read_bytes())

    def link(self,path,target,directory=False):
        try:path.symlink_to(target,target_is_directory=directory)
        except OSError:self.skipTest('Symlink creation unavailable')

    def test_file_symlink_refused(self):
        outside=self.root/'outside.heic';shutil.copyfile(self.source/'sample1.heic',outside)
        (self.source/'sample1.heic').unlink();self.link(self.source/'sample1.heic',outside)
        with self.assertRaises(OSError):self.convert()

    def test_root_symlink_refused(self):
        link=self.root/'linked';self.link(link,self.source,True)
        with self.assertRaises(OSError):self.convert(link)

    def test_linked_parent_refused(self):
        link=self.root/'linked';self.link(link,self.root,True)
        with self.assertRaises(OSError):self.convert(link/'photos')

    def test_dangling_output_link_refused(self):
        target=self.root/'absent';self.link(self.out,target)
        with self.assertRaises(FileExistsError):self.convert()
        self.assertFalse(target.exists())

    def test_setup_linked_parent_refused(self):
        link=self.root/'linked';self.link(link,self.root,True)
        with self.assertRaises(OSError):make_sample.make(link/'new')
        self.assertFalse((self.root/'new').exists())

    def test_fifo_refused_without_external_decode(self):
        if not hasattr(os,'mkfifo'):self.skipTest('Unix pipes unavailable')
        os.mkfifo(self.source/'pipe.heic')
        with patch.object(subprocess,'run',side_effect=AssertionError('Must refuse before decode')):
            with self.assertRaises(OSError):self.convert()

    def test_traversal_refused(self):
        with self.assertRaises(OSError):self.convert(self.source/'..'/'photos')
        with self.assertRaises(OSError):self.convert(destination=self.root/'..'/self.root.name/'jpgs')

    def test_missing_executable_refused_before_output_creation(self):
        with self.assertRaises(OSError):tool.convert(self.source,self.out,'__missing_magick_executable__')
        self.assertFalse(self.out.exists())

    def test_output_inside_source_refused_before_any_creation(self):
        destination=self.source/'jpgs'
        before=state(self.source)
        with self.assertRaises(OSError):self.convert(destination=destination)
        self.assertFalse(destination.exists())
        self.assertEqual(before,state(self.source))

    def test_more_than_100_entries_refused(self):
        for i in range(101): (self.source/f'x{i}.heic').write_bytes(b'fixture')
        with self.assertRaises(OSError):self.convert()
        self.assertFalse(self.out.exists())

    def test_oversized_source_refused_before_reading(self):
        with (self.source/'sample1.heic').open('wb') as handle:handle.truncate(25*1024*1024+1)
        with self.assertRaises(OSError):self.convert()
        self.assertFalse(self.out.exists())

    def test_source_inventory_change_refused_after_copy(self):
        real=subprocess.run;n=0
        def changed(args,**kwargs):
            nonlocal n
            result=real(args,**kwargs)
            if 'JPEG:-' in args:
                n+=1
                if n==3:(self.source/'sample1.heic').write_bytes(b'changed by simulated other software')
            return result
        with patch.object(subprocess,'run',side_effect=changed):
            with self.assertRaisesRegex(OSError,'changed'):self.convert()

    def test_invalid_generated_bytes_refused_before_output_file(self):
        real=subprocess.run
        def bad(args,**kwargs):
            if 'JPEG:-' in args:return subprocess.CompletedProcess(args,0,b'NOT JPEG',b'')
            return real(args,**kwargs)
        with patch.object(subprocess,'run',side_effect=bad):
            with self.assertRaises(OSError):self.convert()
        self.assertFalse((self.out/'sample1.jpg').exists())

    def test_partial_failure_keeps_completed_output_and_originals(self):
        real=subprocess.run;before=state(self.source);n=0
        def injected(args,**kwargs):
            nonlocal n
            if 'JPEG:-' in args:
                n+=1
                if n==2:return subprocess.CompletedProcess(args,1,b'',b'injected failure')
            return real(args,**kwargs)
        with patch.object(subprocess,'run',side_effect=injected):
            with self.assertRaises(OSError):self.convert()
        self.assertEqual(before,state(self.source))
        self.assertTrue((self.out/'sample1.jpg').is_file())
        self.assertFalse((self.out/'sample2.jpg').exists())
        with self.assertRaises(FileExistsError):self.convert()


if __name__=='__main__':unittest.main()
