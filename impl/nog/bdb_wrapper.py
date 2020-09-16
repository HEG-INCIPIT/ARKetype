import logging

import hjson
import pathlib2

import nog.bdb
import nog.exc

log = logging.getLogger(__name__)


class BdbWrapper(object):
    """Wrap a minter BerkeleyDB and provide more convenient access to the values used by EZID.
    Values are available as attributes with more descriptive names and strings parsed to
    ints and lists as needed. """

    def __init__(self, bdb_path, is_new=False, dry_run=False):
        self._bdb = Bdb(bdb_path, is_new, dry_run)
        # self._bdb = bdb
        self._is_new = is_new
        self._dry_run = dry_run

    def __enter__(self):
        self._bdb.__enter__()
        if self._is_new:
            return self._init_new()
        else:
            return self._init_existing()

    def _init_new(self):
        bdb = self._bdb
        bdb.set('basecount', 0)
        bdb.set('oacounter', 0)
        bdb.set('oatop', 0)
        bdb.set('total', 0)
        bdb.set('percounter', 0)
        bdb.set('template', '')
        bdb.set('mask', '')
        bdb.set('atlast', '')
        bdb.set_list('saclist', [])
        bdb.set_list('siclist', [])

        # Values not used by the EZID minter. We set them to increase the chance that
        # the minter can be read by N2T or other implementations.
        bdb.set('addcheckchar', 1)
        bdb.set('atlast_status', 3)
        bdb.set('dbversion', 'Generated by EZID')
        bdb.set('erc', 'Generated by EZID')
        bdb.set('expandable', 1)
        bdb.set('fseqnum', 1)
        bdb.set('generator_type', 'random')
        bdb.set('germ', 0)
        bdb.set('gseqnum', 1)
        bdb.set('gseqnum_date', 0)
        bdb.set('held', 0)
        bdb.set('lzskipcount', 0)
        bdb.set('maskskipcount', 0)
        bdb.set('oklz', 1)
        bdb.set('padwidth', '20')
        bdb.set('queued', 0)
        bdb.set('status', 'e')
        bdb.set('type', 'rand')
        bdb.set('unbounded', 1)
        bdb.set('version', '0.1.0')
        return self._init_existing()

    def _init_existing(self):
        bdb = self._bdb
        self.base_count = bdb.get_int('basecount')
        self.combined_count = bdb.get_int('oacounter')
        self.max_combined_count = bdb.get_int('oatop')
        self.total_count = bdb.get_int('total')
        self.max_per_counter = bdb.get_int('percounter')
        self.template_str = bdb.get('template')
        self.mask_str = bdb.get('mask')
        self.atlast_str = bdb.get('atlast')
        self.active_counter_list = bdb.get_list('saclist')
        self.inactive_counter_list = bdb.get_list('siclist')
        self.counter_list = []
        i = 0
        while True:
            try:
                self.counter_list.append(
                    (
                        bdb.get_int('c{}/top'.format(i)),
                        bdb.get_int('c{}/value'.format(i)),
                    )
                )
            except KeyError:
                break
            i += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._dry_run:
            log.debug(
                'Dry-run: Minter state not saved. Any minted IDs will be repeated.'
            )
            return
        if exc_type in (StopIteration, GeneratorExit):
            return
        if exc_type:
            log.error(
                'Minter state not written back to BerkeleyDB due to exception. '
                'Any minted IDs will be repeated.'
            )
            return
        bdb = self._bdb
        bdb.set('basecount', self.base_count)
        bdb.set('oacounter', self.combined_count)
        bdb.set('oatop', self.max_combined_count)
        bdb.set('total', self.total_count)
        bdb.set('percounter', self.max_per_counter)
        bdb.set('template', self.template_str)
        bdb.set('mask', self.mask_str)
        bdb.set('atlast', self.atlast_str)
        bdb.set_list('saclist', self.active_counter_list)
        bdb.set_list('siclist', self.inactive_counter_list)
        for n, (top, value) in enumerate(self.counter_list):
            bdb.set('c{}/top'.format(n), top),
            bdb.set('c{}/value'.format(n), value),
        self._bdb.__exit__(exc_type, exc_val, exc_tb)

    def as_hjson(self, compact=True):
        d = self.as_dict(compact)
        return hjson.dumps(d, indent=2)  # , sort_keys=True, item_sort_key=_sort_key,)

    def as_dict(self, compact=True):
        """Get the state of a minter BerkeleyDB as a dict. Only the fields used by EZID are
        included.
        """
        d = {
            'base_count': self.base_count,
            'combined_count': self.combined_count,
            'max_combined_count': self.max_combined_count,
            'total_count': self.total_count,
            'max_per_counter': self.max_per_counter,
            'template_str': self.template_str,
            'mask_str': self.mask_str,
            'atlast_str': self.atlast_str,
            'active_counter_list': self.active_counter_list,
            'inactive_counter_list': self.inactive_counter_list,
            'counter_list': self.counter_list,
        }
        if compact:
            for k in ('counter_list', 'active_counter_list', 'inactive_counter_list'):
                d[k] = str(d[k])
        return d


class Bdb:
    def __init__(self, bdb_path, is_new=False, dry_run=False, debug=False):
        """Context manager for a BerkeleyDB.

        Wrap a BerkeleyDB in a context manager that provides:

        - A holding area (a second dict) where all changes are stored until the context
          is exited. This is to prevent changes from being written back to the database
          in case the minter is interrupted. This again is because an incomplete minting
          should cause the sequence of identifiers to be repeated the next time the
          minter is used.
        - Basic methods for opening and closing the database file
        - Basic type conversions / parsing.

        Args:
            bdb_path (str or pathlib2.Path): Path to a BerkeleyDB minter database file.
            is_new:
            dry_run:
        """
        if not debug:
            log.setLevel(logging.INFO)

        log.debug(
            'Creating BerkeleyDB context manager. is_new={} dry_run={}'.format(
                is_new, dry_run
            )
        )
        self._bdb_path = pathlib2.Path(bdb_path)
        self._is_new = is_new
        self._dry_run = dry_run
        self._bdb_obj = None
        self._bdb_dict = None

    def __enter__(self):
        self._bdb_obj = nog.bdb.open_bdb(self._bdb_path, self._is_new)
        self._bdb_dict = dict(self._bdb_obj)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._dry_run:
            log.debug(
                'Dry-run: Minter state not saved. Any minted IDs will be repeated.'
            )
            return
        if exc_type in (StopIteration, GeneratorExit):
            return
        if exc_type:
            log.error(
                'Minter state not written back to BerkeleyDB due to exception. '
                'Any minted IDs will be repeated.'
            )
            return
        self._bdb_obj.update(self._bdb_dict)
        self._bdb_obj.sync()
        self._bdb_obj.close()
        log.debug('BerkeleyDB updated: {}'.format(self._bdb_path.as_posix()))

    def as_dict(self):
        return self._bdb_dict

    def get(self, key_str):
        # return self._bdb[self._key(key_str)].decode("ascii") # Py3
        v = self._bdb_dict[self._key(key_str)]
        if '/top' not in key_str and '/value' not in key_str:
            log.debug("BDB: {} -> {}".format(key_str, v))
        return v

    def get_int(self, key_str):
        return int(self.get(key_str))

    def get_list(self, key_str):
        """Read a space separated string to a list"""
        return self.get(key_str).split()

    def set(self, key_str, value):
        # self._bdb[self._key(key_str)] = str(value).encode("ascii") # Py3
        v = str(value)
        k = self._key(key_str)
        # assert k in self._bdb, 'Attempted to write unknown key: to key not present in BerkeleyDB'
        self._bdb_dict[k] = v
        if '/top' not in key_str and '/value' not in key_str:
            log.debug("BDB: {} <- {}".format(key_str, v))

    def set_list(self, key_str, value_list):
        """Write list to a space separated string"""
        self.set(key_str, " ".join(value_list))

    def append(self, key_str, append_str):
        """Append to space separated list.
        """
        self.set(key_str, "{} {}".format(self.get(key_str), append_str))

    def pop(self, key_str, idx):
        """Pop from space separated list"""
        lst = self.get_list(key_str)
        s = lst.pop(idx)
        self.set_list(key_str, lst)
        return s

    @staticmethod
    def _key(key_str):
        # return f":/{key_str}".encode("ascii") # Py3
        return ":/{}".format(key_str)
