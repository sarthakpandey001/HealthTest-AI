
import React from 'react';

const historyItems = [
    { title: 'Export to Jiras', detail: 'Anoed theal orate account: 5 sert 1354, 2018 missing details.', time: '12:08' },
    { title: 'TctC.zax-History', detail: 'Count Slitray oer Megilaod 2.2022. Robwickz: 10/8', time: '01:05' },
    { title: 'Fewoit Faxe Hixera', detail: 'Rodewilcz: 10/11', time: '20:15' },
];

export const TestCaseHistory: React.FC = () => {
  return (
    <div>
      <h3 className="text-md font-semibold text-slate-800 mb-3">Test Case History</h3>
      <ul className="space-y-4">
        {historyItems.map((item, index) => (
          <li key={index}>
            <div className="flex justify-between items-baseline">
              <p className="font-semibold text-sm text-slate-700">{item.title}</p>
              <p className="text-xs text-slate-500">{item.time}</p>
            </div>
            <p className="text-sm text-slate-500">{item.detail}</p>
          </li>
        ))}
      </ul>
    </div>
  );
};
