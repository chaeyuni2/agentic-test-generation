from extract_diff import merge_ranges


def test_merge_ranges_adjacent():
    ranges = [(10, 12), (13, 15), (20, 21)]
    assert merge_ranges(ranges) == [(10, 15), (20, 21)]


def test_merge_ranges_overlap():
    ranges = [(5, 10), (8, 12), (30, 31)]
    assert merge_ranges(ranges) == [(5, 12), (30, 31)]


def test_merge_ranges_empty():
    assert merge_ranges([]) == []