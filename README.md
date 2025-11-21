<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# HealthTest-AI

A small toolkit and UI for generating structured QA test cases from natural language requirements using a GenAI backend. This repository contains a React + Vite frontend and lightweight services that call a GenAI model (see `services/geminiService.ts`).

This update documents the recent additions and how to run and access the deployed app.

## What's new (latest changes)
- `services/geminiService.ts` now exposes helper functions used by the UI:
  - `getClarificationQuestions(requirements, openApiSchema?)` — returns 3-5 focused clarifying questions (JSON array of strings).
  - `generateTestCases(requirements, openApiSchema?, clarifications?)` — calls an external RAG service, then asks the GenAI model to return structured test cases and a feature gap analysis (includes traceability for sources).
  - `generateCodeSnippet(testCase)` — generates a small code snippet for the test (curl, Cypress/Playwright, etc.).
  - `suggestAssertions(testCase)` — returns 3-5 suggested assertions for automation.

These functions are designed to produce structured JSON output and include traceability metadata. If your requirements mention patient data, consent, or similar PHI-related topics, the generated test cases will often include traceability tags referencing regulatory sources such as HIPAA and GDPR.

## Live deployment
The app is hosted on Firebase Hosting:

https://gen-ai-hackathon-tc-gen-build.web.app/

Visit that URL to see the most recent deployed UI and try generating test cases without running locally.

## Run locally

Prerequisites: Node.js (LTS recommended), npm, and optionally the Firebase CLI for deployment.

1. Install dependencies

   ```powershell
   npm install
   ```

2. Environment variables

   Create a `.env.local` file at the project root and set your GenAI API key. The project expects the key to be available as `API_KEY` (used by `services/geminiService.ts`). Example:

   ```text
   API_KEY=your_gemini_api_key_here
   ```

3. Run the app in development

   ```powershell
   npm run dev
   ```

4. Build for production

   ```powershell
   npm run build
   ```

5. (Optional) Deploy to Firebase Hosting

   If you want to deploy to Firebase Hosting (the site above was deployed this way), install and login with the Firebase CLI, then run:

   ```powershell
   npm run build
   firebase deploy --only hosting
   ```

   Note: `firebase.json` is present in the repo and contains the hosting configuration used for the live URL above.

## Quick usage examples

Import and call the helpers from `services/geminiService.ts` in a Node/renderer context (example uses the local exported functions — the UI already calls these):

```ts
import { getClarificationQuestions, generateTestCases } from './services/geminiService';

async function example() {
  const requirements = `Create a patient consent endpoint allowing patients to submit, update, revoke consent, support deletion and portability requests.`;
  const clarifications = await getClarificationQuestions(requirements);
  console.log('Clarification questions:', clarifications);

  const { testCases, featureGaps } = await generateTestCases(requirements, undefined, clarifications.join('\n'));
  console.log('Generated test cases:', testCases);
  console.log('Feature gaps:', featureGaps);
}

example().catch(console.error);
```

Notes:
- The RAG (retrieval-augmented generation) step used by `generateTestCases` calls an external endpoint to gather context/source URIs. The returned `traceability` field will contain those source URIs or `N/A`.
- If your requirements reference patient data, consent, geographical restrictions, or data-subject rights, the generated output should include references to applicable regulations (e.g., HIPAA, GDPR) in the traceability results.

## Contributing

If you add features or change environment names (for example renaming `API_KEY`), update this README and the `.env` handling in `services/geminiService.ts` accordingly.

## License

This project is provided as-is. See `metadata.json` for author/project metadata.
