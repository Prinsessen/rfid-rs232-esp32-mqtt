// Host test of rfid_frame.h: g++ -std=c++17 -Wall -I. tests/rfid_frame_test.cpp -o /tmp/rfid_frame_test && /tmp/rfid_frame_test
// The tags here are made up; only their checksums are right (the house's tags are in openHAB, never here).
#include "rfid_frame.h"
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

static int fails = 0, checks = 0;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

struct Got { std::vector<std::string> ok; int bad = 0; };

// feeds s one byte per ms starting at t, then calls idle() 200 ms later
static Got run(rfid::Frame &f, const std::string &s, uint32_t t = 1000, bool idle_after = true) {
  Got g;
  auto take = [&](rfid::Frame::Result r) {
    if (r == rfid::Frame::OK) g.ok.push_back(f.uid());
    if (r == rfid::Frame::BAD) g.bad++;
  };
  for (unsigned char c : s) take(f.feed(c, t++));
  if (idle_after) take(f.idle(t + 200));
  return g;
}

// a 12-digit frame body with a correct XOR checksum for these 5 bytes
static std::string tag(const char *id10) {
  unsigned x = 0, b;
  for (int i = 0; i < 5; i++) { sscanf(id10 + 2 * i, "%2x", &b); x ^= b; }
  char s[13];
  snprintf(s, sizeof s, "%s%02X", id10, x);
  return s;
}

int main() {
  const std::string A = tag("0101A2B3C4"), B = tag("0F00112233");

  { rfid::Frame f; Got g = run(f, A + "\r\n");                  // the format a serial-to-Ethernet box passed on
    CHECK(g.ok.size() == 1 && g.ok[0] == A && g.bad == 0); }
  { rfid::Frame f; Got g = run(f, "\x02" + A + "\r\n\x03");     // STX/ETX framed: once, not three times
    CHECK(g.ok.size() == 1 && g.ok[0] == A && g.bad == 0); }
  { rfid::Frame f; std::string s = A + "\r\n"; s.push_back('\0'); s.push_back('\0');
    Got g = run(f, s);                                           // a serial box's NUL padding
    CHECK(g.ok.size() == 1 && g.bad == 0); }
  { rfid::Frame f; std::string low = A; for (auto &c : low) c = tolower(c);
    Got g = run(f, low + "\r\n");                                // lower case comes out upper case
    CHECK(g.ok.size() == 1 && g.ok[0] == A); }
  { rfid::Frame f; std::string bad = A; bad[11] = bad[11] == '0' ? '1' : '0';
    Got g = run(f, bad + "\r\n");                                // one wrong digit: never reaches openHAB
    CHECK(g.ok.empty() && g.bad == 1); }
  { rfid::Frame f; Got g = run(f, A.substr(0, 11) + "\r\n");     // 11 digits
    CHECK(g.ok.empty() && g.bad == 1); }
  { rfid::Frame f; Got g = run(f, "0" + A + "\r\n");             // 13 digits (the last 12 would pass the checksum)
    CHECK(g.ok.empty() && g.bad == 1); }
  { rfid::Frame f; Got g = run(f, A);                            // no terminator: the pause ends it
    CHECK(g.ok.size() == 1 && g.ok[0] == A); }
  { rfid::Frame f; Got g = run(f, A, 1000, false);               // ...but not before the pause
    CHECK(g.ok.empty() && g.bad == 0); }
  { rfid::Frame f; Got g;                                        // a broken beginning, a pause, a whole frame
    Got g1 = run(f, A.substr(0, 5), 1000, false);
    Got g2 = run(f, A + "\r\n", 2000, false);
    CHECK(g1.ok.empty() && g2.ok.size() == 1 && g2.ok[0] == A && g2.bad == 1); }
  { rfid::Frame f; Got g = run(f, A + "\r\n" + B + "\r\n");      // two tags back to back
    CHECK(g.ok.size() == 2 && g.ok[0] == A && g.ok[1] == B); }
  { rfid::Frame f; Got g = run(f, "\r\n\r\n\x03\x02");           // terminators alone are nothing
    CHECK(g.ok.empty() && g.bad == 0); }
  { rfid::Frame f; uint32_t t = 0xFFFFFFF0u;                     // millis() wrapping mid-frame
    Got g = run(f, A + "\r\n", t);
    CHECK(g.ok.size() == 1); }

  { rfid::Debounce d;                                            // a held tag repeats: one reading
    CHECK(d.accept(A.c_str(), 1000));
    CHECK(!d.accept(A.c_str(), 2000));
    CHECK(!d.accept(A.c_str(), 4500));                           // sliding: 2.5 s after the LAST read
    CHECK(d.accept(A.c_str(), 7600)); }                          // away > 3 s, shown again: a new reading
  { rfid::Debounce d;                                            // another tag always passes
    CHECK(d.accept(A.c_str(), 1000));
    CHECK(d.accept(B.c_str(), 1100));
    CHECK(d.accept(A.c_str(), 1200)); }
  { rfid::Debounce d;                                            // the very first reading at t = 0
    CHECK(d.accept(A.c_str(), 0)); }

  printf("%d checks, %d failed\n", checks, fails);
  return fails ? 1 : 0;
}
