injected_javascript = '''
// overwrite the `languages` property to use a custom getter
Object.defineProperty(navigator, "languages", {
  get: function() {
    return ["zh-CN","zh","zh-TW","en-US","en"];
  }
});

// Overwrite the `plugins` property to use a custom getter.
Object.defineProperty(navigator, 'plugins', {
  get: () => [1, 2, 3, 4, 5],
});

// Pass the Webdriver test
Object.defineProperty(navigator, 'webdriver', {
  get: () => undefined,
});


// Pass the Chrome Test.
// We can mock this in as much depth as we need for the test.
window.navigator.chrome = {
  runtime: {},
  // etc.
};

// Pass the Permissions Test.
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
  parameters.name === 'notifications' ?
    Promise.resolve({ state: Notification.permission }) :
    originalQuery(parameters)
);
'''
