import React from 'react';

test('basic test to ensure Jest is working', () => {
  expect(1 + 1).toBe(2);
});

test('React import works', () => {
  expect(React).toBeDefined();
});