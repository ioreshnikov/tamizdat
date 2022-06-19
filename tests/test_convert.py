from tamizdat.convert import convert_book, prepare_cover

from faker import Faker

from unittest import TestCase
from unittest.mock import patch, Mock


fake = Faker()


class ConvertTestCase(TestCase):
    @patch("subprocess.check_call")
    @patch("os.path.exists")
    def test_convert_book_exits_if_output_already_exists(self, mock_path_exists, mock_check_call):
        book = Mock()
        mock_path_exists.return_value = True

        convert_book(book)
        mock_check_call.assert_not_called()

    @patch("tamizdat.convert.prepare_cover")
    @patch("subprocess.check_call")
    @patch("os.path.exists")
    def test_convert_book_golden_path(self, mock_path_exists, mock_check_call, mock_prepare_cover):
        fake = Faker()

        book = Mock()
        book_id = fake.random.randint(100, 1000000)
        book.ebook_fb2.local_path = "{}.fb2.zip".format(book_id)
        mock_path_exists.return_value = False

        convert_book(book)

        # XXX: So what's going on in here. call_args is a tuple of
        # (args, kwargs). args itself is a tuple of arguments, which
        # in our case is a 1-tuple. And in there we finally have a
        # command passed to check_call in the form of an argument
        # list.
        arglist = mock_check_call.call_args[0][0]
        command, input_file, output_file, *_ = arglist

        self.assertEqual(command, "ebook-convert")
        self.assertEqual(input_file, book.ebook_fb2.local_path)
        self.assertEqual(output_file, "{}.epub".format(book_id))

    @patch("tamizdat.convert.prepare_cover")
    @patch("subprocess.check_call")
    @patch("os.path.exists")
    def test_convert_book_does_not_attach_a_cover_if_there_is_none(self, mock_path_exists, mock_check_call, mock_prepare_cover):
        fake = Faker()

        book = Mock()
        book_id = fake.random.randint(100, 1000000)
        book.ebook_fb2.local_path = "{}.fb2.zip".format(book_id)
        mock_path_exists.return_value = False
        mock_prepare_cover.return_value = None

        convert_book(book)

        arglist, *_ = mock_check_call.call_args.args
        for arg in arglist:
            self.assertFalse(arg.startswith("--cover"))


class PrepareCoverTestCase(TestCase):
    def test_prepare_cover_returns_none_if_book_has_no_cover(self):
        book = Mock()
        book.cover_image = None

        cover_path = prepare_cover(book)

        self.assertIsNone(cover_path)

    @patch("subprocess.check_call")
    def test_prepare_cover_golden_path(self, mock_check_call):
        book = Mock()
        book_id = fake.random.randint(100, 1000000)
        book.cover_image.local_path = "{}.jpg".format(book_id)

        return_path = prepare_cover(book)

        # XXX: See the comment in test_convert_book_golden_path.
        arglist = mock_check_call.call_args[0][0]
        command, input_path, *_, output_path = arglist

        self.assertEqual(command, "convert")
        self.assertEqual(input_path, book.cover_image.local_path)
        self.assertEqual(output_path, return_path)
