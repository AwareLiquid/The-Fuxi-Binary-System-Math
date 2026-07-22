"""The King Wen sequence as machine-readable data.

Provenance
----------
This table was reconciled across four independent line-data sources and then
put through eight structural checks. The sources and their native conventions:

* Wikipedia, *List of hexagrams of the I Ching* -- explicit inner/outer trigram
  labels, no reversal needed.
* zh.wikipedia, 六十四卦 -- used only for the unordered trigram pair, because
  the retrieved table's trigram order was unreliable.
* adamblvck/iching-wilhelm-dataset and the krry hexagrams gist -- both encode
  the top line first, so both were reversed.
* urschrei/hexagrams -- natively bottom-line-first, which made it the useful
  orientation witness. It carries three defects and was not used as an
  authority: hexagram 27 is encoded as hexagram 17's pattern, and hexagrams 1
  and 8 are lost to dictionary key collisions. Its hexagram 27 value is
  outvoted three to one and is rejected by the structural checks below.

Orientation was pinned independently of any source by three probes: hexagram 24
has its single yang line at the bottom, hexagram 23 has its single yang line at
the top, and hexagram 11 is Earth over Heaven so its lower trigram is Qian.

The trigram-to-bit map is fixed by the classical mnemonic 八卦取象歌, in which
兌上缺 (Dui broken above) and 巽下斷 (Xun broken below) are the decisive
clauses.

Structural checks, all passing
------------------------------
A. The 64 values are exactly the set {0, ..., 63}, each once.
B. Hexagram 1 is all yang and hexagram 2 is all yin.
C. Hexagrams 63 and 64 are the two alternating patterns.
D. The couplet structure: 28 reversal pairs and 4 complement pairs, none
   unexplained. The 8 palindromic hexagrams are 1, 2, 27, 28, 29, 30, 61, 62.
E. The twelve sovereign hexagrams (十二消息卦) show yang waxing from the bottom
   and then yin waxing from the bottom.
F. The eight doubled-trigram hexagrams sit at 1, 2, 29, 30, 51, 52, 57, 58.
G. Reading the bottom line as the most significant bit and sorting descending
   reproduces the Shao Yong (Earlier Heaven) order across all 64 positions.
H. The perimeter of the 8x8 Earlier Heaven square is the expected 28-hexagram
   set.

Checks A through D alone are not sufficient. Reversing the bits within each
trigram, which swaps Dui with Xun and Zhen with Gen while leaving the trigram
placement alone, passes all four. Checks E, F and G detect it.

English names follow Wilhelm and Baynes. The Unicode character names differ for
several hexagrams and are not used here. The Unicode glyph for King Wen number
n is chr(0x4DBF + n); that block is contiguous and in King Wen order.
"""

from __future__ import annotations

from .encoding import lines_to_value

#: King Wen sequence. Index = King Wen number - 1.
#: Each entry is (lines_bottom_first, chinese_name, english_name).
#: lines[0] is the bottom (initial) line; lines[5] is the top line.
#: 1 is yang, 0 is yin.
KING_WEN = [
    ((1, 1, 1, 1, 1, 1), "乾", "The Creative"),
    ((0, 0, 0, 0, 0, 0), "坤", "The Receptive"),
    ((1, 0, 0, 0, 1, 0), "屯", "Difficulty at the Beginning"),
    ((0, 1, 0, 0, 0, 1), "蒙", "Youthful Folly"),
    ((1, 1, 1, 0, 1, 0), "需", "Waiting"),
    ((0, 1, 0, 1, 1, 1), "訟", "Conflict"),
    ((0, 1, 0, 0, 0, 0), "師", "The Army"),
    ((0, 0, 0, 0, 1, 0), "比", "Holding Together"),
    ((1, 1, 1, 0, 1, 1), "小畜", "The Taming Power of the Small"),
    ((1, 1, 0, 1, 1, 1), "履", "Treading"),
    ((1, 1, 1, 0, 0, 0), "泰", "Peace"),
    ((0, 0, 0, 1, 1, 1), "否", "Standstill"),
    ((1, 0, 1, 1, 1, 1), "同人", "Fellowship with Men"),
    ((1, 1, 1, 1, 0, 1), "大有", "Possession in Great Measure"),
    ((0, 0, 1, 0, 0, 0), "謙", "Modesty"),
    ((0, 0, 0, 1, 0, 0), "豫", "Enthusiasm"),
    ((1, 0, 0, 1, 1, 0), "隨", "Following"),
    ((0, 1, 1, 0, 0, 1), "蠱", "Work on What Has Been Spoiled"),
    ((1, 1, 0, 0, 0, 0), "臨", "Approach"),
    ((0, 0, 0, 0, 1, 1), "觀", "Contemplation"),
    ((1, 0, 0, 1, 0, 1), "噬嗑", "Biting Through"),
    ((1, 0, 1, 0, 0, 1), "賁", "Grace"),
    ((0, 0, 0, 0, 0, 1), "剝", "Splitting Apart"),
    ((1, 0, 0, 0, 0, 0), "復", "Return"),
    ((1, 0, 0, 1, 1, 1), "无妄", "Innocence"),
    ((1, 1, 1, 0, 0, 1), "大畜", "The Taming Power of the Great"),
    ((1, 0, 0, 0, 0, 1), "頤", "The Corners of the Mouth"),
    ((0, 1, 1, 1, 1, 0), "大過", "Preponderance of the Great"),
    ((0, 1, 0, 0, 1, 0), "坎", "The Abysmal (Water)"),
    ((1, 0, 1, 1, 0, 1), "離", "The Clinging (Fire)"),
    ((0, 0, 1, 1, 1, 0), "咸", "Influence"),
    ((0, 1, 1, 1, 0, 0), "恆", "Duration"),
    ((0, 0, 1, 1, 1, 1), "遯", "Retreat"),
    ((1, 1, 1, 1, 0, 0), "大壯", "The Power of the Great"),
    ((0, 0, 0, 1, 0, 1), "晉", "Progress"),
    ((1, 0, 1, 0, 0, 0), "明夷", "Darkening of the Light"),
    ((1, 0, 1, 0, 1, 1), "家人", "The Family"),
    ((1, 1, 0, 1, 0, 1), "睽", "Opposition"),
    ((0, 0, 1, 0, 1, 0), "蹇", "Obstruction"),
    ((0, 1, 0, 1, 0, 0), "解", "Deliverance"),
    ((1, 1, 0, 0, 0, 1), "損", "Decrease"),
    ((1, 0, 0, 0, 1, 1), "益", "Increase"),
    ((1, 1, 1, 1, 1, 0), "夬", "Breakthrough"),
    ((0, 1, 1, 1, 1, 1), "姤", "Coming to Meet"),
    ((0, 0, 0, 1, 1, 0), "萃", "Gathering Together"),
    ((0, 1, 1, 0, 0, 0), "升", "Pushing Upward"),
    ((0, 1, 0, 1, 1, 0), "困", "Oppression"),
    ((0, 1, 1, 0, 1, 0), "井", "The Well"),
    ((1, 0, 1, 1, 1, 0), "革", "Revolution"),
    ((0, 1, 1, 1, 0, 1), "鼎", "The Cauldron"),
    ((1, 0, 0, 1, 0, 0), "震", "The Arousing (Shock, Thunder)"),
    ((0, 0, 1, 0, 0, 1), "艮", "Keeping Still (Mountain)"),
    ((0, 0, 1, 0, 1, 1), "漸", "Development (Gradual Progress)"),
    ((1, 1, 0, 1, 0, 0), "歸妹", "The Marrying Maiden"),
    ((1, 0, 1, 1, 0, 0), "豐", "Abundance"),
    ((0, 0, 1, 1, 0, 1), "旅", "The Wanderer"),
    ((0, 1, 1, 0, 1, 1), "巽", "The Gentle (Wind)"),
    ((1, 1, 0, 1, 1, 0), "兌", "The Joyous (Lake)"),
    ((0, 1, 0, 0, 1, 1), "渙", "Dispersion"),
    ((1, 1, 0, 0, 1, 0), "節", "Limitation"),
    ((1, 1, 0, 0, 1, 1), "中孚", "Inner Truth"),
    ((0, 0, 1, 1, 0, 0), "小過", "Preponderance of the Small"),
    ((1, 0, 1, 0, 1, 0), "既濟", "After Completion"),
    ((0, 1, 0, 1, 0, 1), "未濟", "Before Completion"),
]

assert len(KING_WEN) == 64, "King Wen table must have 64 entries"


def king_wen_ordering() -> list:
    """The 64 hexagram values in King Wen order."""
    return [lines_to_value(lines) for lines, _, _ in KING_WEN]


def name(number: int) -> tuple:
    """(chinese, english) for a King Wen number in 1..64."""
    if not 1 <= number <= 64:
        raise ValueError("King Wen number must be in 1..64")
    _, zh, en = KING_WEN[number - 1]
    return zh, en


def number_of(value: int) -> int:
    """The King Wen number of a hexagram value."""
    order = king_wen_ordering()
    return order.index(value) + 1


def unicode_glyph(number: int) -> str:
    """The Unicode hexagram symbol for a King Wen number."""
    if not 1 <= number <= 64:
        raise ValueError("King Wen number must be in 1..64")
    return chr(0x4DBF + number)


#: The twelve sovereign hexagrams (十二消息卦), by King Wen number, in the order
#: yang waxes from the bottom and then yin waxes from the bottom. Used as a
#: structural check on the table.
SOVEREIGN_HEXAGRAMS = (24, 19, 11, 34, 43, 1, 44, 33, 12, 20, 23, 2)

#: The eight doubled-trigram hexagrams (八純卦), by King Wen number.
DOUBLED_TRIGRAM_HEXAGRAMS = (1, 2, 29, 30, 51, 52, 57, 58)
