export enum Priority {
  High = 'High',
  Medium = 'Medium',
  Low = 'Low',
}

export enum Status {
  Draft = 'Draft',
  Ready = 'Ready',
  InProgress = 'In Progress',
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
}

export interface User {
  id: string;
  email: string;
}
