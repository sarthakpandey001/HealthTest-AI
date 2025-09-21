import { TestCase } from '../types';

function downloadFile(content: string, fileName: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = fileName;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function escapeCsvCell(cellData: string) {
  // If the cell data contains a comma, newline, or double quote, wrap it in double quotes.
  if (/[",\n]/.test(cellData)) {
    // Also, double up any existing double quotes.
    return `"${cellData.replace(/"/g, '""')}"`;
  }
  return cellData;
}

export function exportTestCasesToCSV(testCases: TestCase[]): void {
  if (testCases.length === 0) {
    return;
  }
  
  const headers = [
    'id', 'title', 'description', 'type', 'priority', 'status',
    'preconditions', 'steps', 'expectedResults'
  ];

  const rows = testCases.map(tc => {
    const row = [
      tc.id,
      tc.title,
      tc.description,
      tc.type,
      tc.priority,
      tc.status,
      tc.preconditions.join('\n'), // Join array items into a single string
      tc.steps.join('\n'),
      tc.expectedResults.join('\n')
    ];
    return row.map(escapeCsvCell).join(',');
  });

  const csvContent = [headers.join(','), ...rows].join('\n');
  downloadFile(csvContent, 'test-cases.csv', 'text/csv;charset=utf-8;');
}

export function exportTestCasesToJSON(testCases: TestCase[]): void {
  if (testCases.length === 0) {
    return;
  }
  
  const jsonContent = JSON.stringify(testCases, null, 2);
  downloadFile(jsonContent, 'test-cases.json', 'application/json;charset=utf-8;');
}
