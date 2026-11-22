// rfid_frame.h - one reading from the Pegasus PP-30/nR2's RS-232 output (2026-11-21)
//
// What the reader sends (seen for years through a serial-to-Ethernet box, and through a
// Python listener): ASCII, 12 hex digits + CR LF, e.g. "123456789A92\r\n".
// The 12 digits are the EM4100 tag's 10-digit ID + a 2-digit XOR checksum of its 5 bytes
// (12^34^56^78^9A = 92; an invented tag). openHAB's KNOWN_TAGS hold all 12, so all 12 are passed on.
//
// Frame: hex digits, ended by anything that is not one (CR, LF, STX/ETX, a serial box's
// NUL padding) or by a pause of GAP_MS. Accepted only as exactly 12 digits with a correct
// checksum: a misread at the door must never reach the alarm.
//
// Debounce: the same UID again within HOLD_MS of its LAST reading is the same presentation
// (a tag held at the reader repeats). It is a sliding window, so a held tag
// gives one reading, not one every 3 s; a different UID always passes.
//
// Host test: g++ -std=c++17 -Wall -I. tests/rfid_frame_test.cpp -o /tmp/rfid_frame_test && /tmp/rfid_frame_test
#pragma once
#include <cstdint>
#include <cstring>

namespace rfid {

static const uint32_t GAP_MS = 100;    // 12 chars + CRLF at 9600 baud take ~15 ms
static const uint32_t HOLD_MS = 3000;  // as the Python listener's debounce_seconds

inline int hexval(uint8_t c) {
  if (c >= '0' && c <= '9') return c - '0';
  if (c >= 'A' && c <= 'F') return c - 'A' + 10;
  if (c >= 'a' && c <= 'f') return c - 'a' + 10;
  return -1;
}

// 12 hex digits: 5 ID bytes, then their XOR
inline bool checksum_ok(const char *d) {
  uint8_t x = 0;
  for (int i = 0; i < 5; i++) x ^= (uint8_t) (hexval(d[2 * i]) << 4 | hexval(d[2 * i + 1]));
  return x == (uint8_t) (hexval(d[10]) << 4 | hexval(d[11]));
}

class Frame {
 public:
  enum Result { MORE, OK, BAD };

  Result feed(uint8_t c, uint32_t now_ms) {
    Result r = MORE;
    if (n_ > 0 && now_ms - last_ms_ > GAP_MS) r = finish();  // a stale beginning ends on its own
    last_ms_ = now_ms;
    const int v = hexval(c);
    if (v >= 0) {
      if (n_ < 12) buf_[n_] = (char) (v < 10 ? '0' + v : 'A' + v - 10);
      n_++;  // counts past 12, so 13 digits is not a frame
      return r;
    }
    return r != MORE ? r : finish();
  }

  // called every loop: a frame without a terminator ends after GAP_MS of silence
  Result idle(uint32_t now_ms) {
    return (n_ > 0 && now_ms - last_ms_ > GAP_MS) ? finish() : MORE;
  }

  const char *uid() const { return uid_; }

 private:
  Result finish() {
    if (n_ == 0) return MORE;  // LF after CR, ETX after CRLF, padding
    const bool ok = n_ == 12 && checksum_ok(buf_);
    if (ok) { memcpy(uid_, buf_, 12); uid_[12] = 0; }
    n_ = 0;
    return ok ? OK : BAD;
  }
  char buf_[12] = {0};
  char uid_[13] = {0};
  uint16_t n_ = 0;
  uint32_t last_ms_ = 0;
};

class Debounce {
 public:
  explicit Debounce(uint32_t hold_ms = HOLD_MS) : hold_ms_(hold_ms) {}
  bool accept(const char *uid, uint32_t now_ms) {
    const bool repeat = seen_ && strcmp(uid, last_) == 0 && now_ms - last_ms_ < hold_ms_;
    strncpy(last_, uid, 12);
    last_[12] = 0;
    last_ms_ = now_ms;
    seen_ = true;
    return !repeat;
  }

 private:
  uint32_t hold_ms_;
  char last_[13] = {0};
  uint32_t last_ms_ = 0;
  bool seen_ = false;
};

}  // namespace rfid
