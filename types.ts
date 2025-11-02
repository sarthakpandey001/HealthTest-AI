export enum Priority {
  High = 'High',
  Medium = 'Medium',
  Low = 'Low',
}

export enum Status {
  Pass = 'Pass',
  Fail = 'Fail',
  Blocked = 'Blocked',
  Draft = 'Draft'
}

export enum TestCaseType {
  Positive = 'Positive',
  Negative = 'Negative',
  Neutral = 'Neutral'
}

export interface TestCase {
  id: string;
  title: string;
  type: TestCaseType;
  priority: Priority;
  status: Status;
  description: string;
  preconditions: string[];
  steps: string[];
  expectedResults: string[];
  traceability: string[];  // Changed to required string array
}

export interface User {
  id: string;
  email: string;
}
