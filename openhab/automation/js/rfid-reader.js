// =============================================================================
// rfid-reader.js - an EXAMPLE openHAB rule (JavaScript Scripting, openhab-js) for rfid-rs232-esp32-mqtt
// =============================================================================
// One reading arrives on the trigger channel mqtt:topic:rfid:tag (openhab/things/rfid_bridge.things):
//   known tag    -> arm or disarm the alarm (toggle), answer "arm" / "disarm"
//   unknown tag  -> leave the alarm alone, answer "denied" (and tell someone - see notify())
// The answer goes to rfid/door/feedback; the bridge turns it into the reader's buzzer (and LED).
//
// Adapt: KNOWN_TAGS, the two alarm items, notify(). Keep:
//   - the trigger channel (no item with an update trigger - a restored state must never toggle an alarm);
//   - the 12-hex check (the firmware checks the checksum, but this rule should not trust anything else);
//   - this rule as the ONE writer of rfid/door/feedback;
//   - never logging a known tag in full: a full EM4100 ID is all it takes to clone the tag.
// =============================================================================
const { rules, triggers, items, actions, time } = require('openhab');

const CHANNEL = 'mqtt:topic:rfid:tag';
const BROKER = 'mqtt:broker:broker';
const FEEDBACK_TOPIC = 'rfid/door/feedback';

// 12 hex digits as the reader sends them: the 10-digit EM4100 ID + its 2-digit XOR checksum.
// This one is invented. Find yours: scan the tag once and read "UNKNOWN tag ..." in openhab.log.
const KNOWN_TAGS = {
  '123456789A92': { name: 'Example card' }
};

function feedback(answer) {
  try {
    const mqtt = actions.Things.getActions('mqtt', BROKER);
    if (mqtt === null || mqtt === undefined) { console.warn('rfid: no MQTT broker actions - "' + answer + '" not sent'); return; }
    mqtt.publishMQTT(FEEDBACK_TOPIC, answer, false);   // never retained: a retained answer would beep at every reconnect
  } catch (e) {
    console.warn('rfid: feedback "' + answer + '" failed: ' + e);   // the alarm was still commanded - the answer is a courtesy
  }
}

function notify(text) {
  // e.g. actions.Things.getActions('mail', 'mail:smtp:mail').sendMail('you@example.org', 'RFID', text)
  console.warn('rfid: ' + text);
}

rules.JSRule({
  name: 'RFID tag scanned',
  description: 'A reading from the RFID bridge: look the tag up, arm/disarm or deny, answer the reader',
  triggers: [triggers.ChannelEventTrigger(CHANNEL)],
  execute: (event) => {
    const tag = String(event.receivedEvent === undefined || event.receivedEvent === null ? '' : event.receivedEvent).trim().toUpperCase();
    if (!/^[0-9A-F]{12}$/.test(tag)) {
      console.warn('rfid: not a tag (' + tag.length + ' chars) - ignored');
      return;
    }
    items.getItem('Rfid_Last_Scan').postUpdate(time.ZonedDateTime.now().toString());
    items.getItem('Rfid_Last_Tag').postUpdate('…' + tag.slice(-4));   // the last four, as in the log

    const known = KNOWN_TAGS[tag];
    if (!known) {
      console.warn('rfid: UNKNOWN tag ' + tag);                     // in full: it is not yours, and you need it to add it
      feedback('denied');
      notify('Unknown RFID tag at the door: ' + tag);
      return;
    }
    const armed = String(items.getItem('Alarm_Armed').state) === 'ON';
    console.info('rfid: ' + known.name + ' (…' + tag.slice(-4) + ') -> ' + (armed ? 'disarming' : 'arming'));
    items.getItem('Alarm_Arm').sendCommand(armed ? 'OFF' : 'ON');
    feedback(armed ? 'disarm' : 'arm');
  }
});
