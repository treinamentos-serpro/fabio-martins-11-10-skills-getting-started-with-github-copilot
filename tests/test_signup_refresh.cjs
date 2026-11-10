const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

class Element {
  constructor() {
    this.children = [];
    this.value = "";
    this.handlers = {};
    this.classList = { add() {} };
  }

  set innerHTML(html) {
    this.html = html;
    this.children = [];
  }

  get options() {
    return this.children;
  }

  appendChild(child) {
    this.children.push(child);
  }

  addEventListener(event, handler) {
    this.handlers[event] = handler;
  }

  setAttribute() {}
}

async function loadApp(signupSucceeds = true) {
  const elements = Object.fromEntries(
    ["activities-list", "activity", "signup-form", "message", "email"].map(
      (id) => [id, new Element()]
    )
  );
  elements.activity.appendChild(new Element());
  elements["signup-form"].reset = () => {
    elements.email.value = "";
    elements.activity.value = "";
  };
  const participants = [];
  const requests = [];
  let initialize;

  vm.runInNewContext(
    fs.readFileSync(path.join(__dirname, "../src/static/app.js"), "utf8"),
    {
      document: {
        getElementById: (id) => elements[id],
        createElement: () => new Element(),
        addEventListener: (_, handler) => { initialize = handler; },
      },
      console,
      setTimeout() {},
      clearTimeout() {},
      async fetch(url, options = {}) {
        requests.push({ url, method: options.method || "GET" });
        if (options.method === "POST") {
          if (!signupSucceeds) {
            return { ok: false, json: async () => ({ detail: "Signup rejected" }) };
          }
          participants.push(new URL(url, "http://localhost").searchParams.get("email"));
          return { ok: true, json: async () => ({ message: "Signed up" }) };
        }
        return {
          ok: true,
          json: async () => ({
            "Chess Club": {
              description: "Play chess",
              schedule: "Friday",
              max_participants: 12,
              participants: [...participants],
            },
          }),
        };
      },
    }
  );

  initialize();
  await new Promise((resolve) => setImmediate(resolve));
  return { elements, requests };
}

test("signup updates participants and available spots without reloading", async () => {
  const { elements, requests } = await loadApp();
  for (const [index, email] of ["first+student@school.edu", "second@school.edu"].entries()) {
    elements.email.value = email;
    elements.activity.value = "Chess Club";
    await elements["signup-form"].handlers.submit({ preventDefault() {} });

    const card = elements["activities-list"].children[0];
    const list = card.children[0].children[1];
    assert.equal(list.children.length, index + 1);
    assert.equal(list.children[index].children[0].textContent, email);
    assert.ok(card.html.includes(`${11 - index} spots left`));
    assert.equal(elements.activity.options.length, 2);
    assert.equal(elements.email.value, "");
  }
  assert.deepEqual(requests.map(({ method }) => method), [
    "GET", "POST", "GET", "POST", "GET",
  ]);
});

test("rejected signup preserves the form and does not change the cards", async () => {
  const { elements, requests } = await loadApp(false);
  const card = elements["activities-list"].children[0];
  elements.email.value = "student@school.edu";
  elements.activity.value = "Chess Club";
  await elements["signup-form"].handlers.submit({ preventDefault() {} });

  assert.equal(elements["activities-list"].children[0], card);
  assert.equal(elements.message.textContent, "Signup rejected");
  assert.equal(elements.message.className, "error");
  assert.equal(elements.email.value, "student@school.edu");
  assert.deepEqual(requests.map(({ method }) => method), ["GET", "POST"]);
});
