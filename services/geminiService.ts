import { GoogleGenAI, Type } from "@google/genai";
import { TestCase } from '../types';

let aiInstance: GoogleGenAI;

// Lazily initialize the AI client to avoid accessing process.env at module load time.
// This prevents the app from crashing if the `process` object is not available immediately.
function getAiClient(): GoogleGenAI {
    if (!aiInstance) {
        // The API key is expected to be set in the execution environment.
        aiInstance = new GoogleGenAI({ apiKey: process.env.API_KEY });
    }
    return aiInstance;
}

const clarificationQuestionsSchema = {
    type: Type.ARRAY,
    description: "A list of questions to ask the user for clarification.",
    items: { type: Type.STRING }
};

const testCaseGenerationSchema = {
    type: Type.OBJECT,
    properties: {
        featureGaps: {
            type: Type.ARRAY,
            description: "A list of strings identifying any remaining ambiguities, missing details, or unclear aspects in the original requirements.",
            items: { type: Type.STRING }
        },
        testCases: {
            type: Type.ARRAY,
            description: "An array of generated test cases.",
            items: {
                type: Type.OBJECT,
                properties: {
                    id: { type: Type.STRING, description: "A unique identifier for the test case, e.g., 'DUS-3-TC01'." },
                    title: { type: Type.STRING, description: "A short, descriptive title for the test case." },
                    description: { type: Type.STRING, description: "A clear explanation of what the test verifies." },
                    type: { type: Type.STRING, enum: ['Positive', 'Negative', 'Neutral'], description: "The category of the test case." },
                    priority: { type: Type.STRING, enum: ['High', 'Medium', 'Low'], description: "The priority of the test case." },
                    status: { type: Type.STRING, enum: ['Draft'], description: "The initial status, always 'Draft'." },
                    preconditions: { type: Type.ARRAY, items: { type: Type.STRING }, description: "Necessary states before the test can run." },
                    steps: { type: Type.ARRAY, items: { type: Type.STRING }, description: "A numbered list of actions to perform." },
                    expectedResults: { type: Type.ARRAY, items: { type: Type.STRING }, description: "The anticipated outcome of each step or the overall test." },
                },
                required: ["id", "title", "description", "type", "priority", "status", "preconditions", "steps", "expectedResults"]
            }
        }
    },
    required: ["featureGaps", "testCases"]
};

export async function getClarificationQuestions(requirements: string, openApiSchema?: string): Promise<string[]> {
    const ai = getAiClient();
    const prompt = `
        You are an expert QA engineer. Your task is to analyze the following software requirements and identify any ambiguities, missing details, or potential edge cases that need clarification before writing test cases.

        Based on the provided requirements (and optional OpenAPI schema), generate a list of 3-5 concise questions to ask the user. These questions should help clarify the requirements and lead to better test cases.

        Return your response as a JSON array of strings, where each string is a question. If no clarification is needed, return an empty array.

        **User Requirements:**
        ---
        ${requirements}
        ---

        ${openApiSchema ? `**OpenAPI Schema (Optional):**\n---\n${openApiSchema}\n---` : ''}

        Example response: ["What should happen if the user enters an incorrect password three times in a row?", "Is there a 'Forgot Password' flow?", "What are the specific password complexity requirements?"]
    `;

    const response = await ai.models.generateContent({
        model: "gemini-2.5-flash",
        contents: prompt,
        config: {
            responseMimeType: "application/json",
            responseSchema: clarificationQuestionsSchema,
        },
    });

    try {
        const jsonText = response.text.trim();
        return JSON.parse(jsonText);
    } catch (e) {
        console.error("Failed to parse clarification questions:", e);
        return [];
    }
}


export async function generateTestCases(requirements: string, openApiSchema?: string, clarifications?: string): Promise<{ testCases: TestCase[]; featureGaps: string[] }> {
    const ai = getAiClient();
    const prompt = `
        You are an expert QA engineer specializing in generating detailed, structured test cases from software requirements.
        Your primary task is to generate a comprehensive set of test cases based on the provided requirements and any additional clarifications.

        **Instructions:**
        1.  Analyze the user requirements below.
        2.  If an OpenAPI schema is provided, use it to understand API endpoints, request/response structures, and constraints for more detailed and accurate test cases.
        3.  If additional clarifications are provided by the user, take them into account to resolve ambiguities.
        4.  For each test case, you **MUST** generate the following fields:
            -   **Test Case ID**: A unique identifier (e.g., 'TC-LOGIN-01').
            -   **Title**: A short, descriptive title.
            -   **Description**: A clear explanation of what the test verifies.
            -   **Test Steps**: A clear, sequential list of actions to perform.
            -   **Expected Results**: The specific, verifiable outcome expected after executing the steps.
            -   **Priority**: Assign a priority of 'High', 'Medium', or 'Low'.
        5.  Also, for each test case, provide:
            -   A category: 'Positive', 'Negative', or 'Neutral'.
            -   An initial status of 'Draft'.
            -   A list of preconditions.
        6.  After generating test cases, identify any remaining ambiguities or gaps in the requirements and list them in a 'Feature Gap Analysis'.
        7.  Return the entire response as a single JSON object matching the provided schema.

        **User Requirements:**
        ---
        ${requirements}
        ---

        ${openApiSchema ? `**OpenAPI Schema (Optional):**\n---\n${openApiSchema}\n---` : ''}
        
        ${clarifications ? `**Additional Clarifications from User:**\n---\n${clarifications}\n---` : ''}
    `;

    const response = await ai.models.generateContent({
        model: "gemini-2.5-flash",
        contents: prompt,
        config: {
            responseMimeType: "application/json",
            responseSchema: testCaseGenerationSchema,
        },
    });

    const jsonText = response.text.trim();
    const parsedResponse = JSON.parse(jsonText);

    return {
        testCases: parsedResponse.testCases || [],
        featureGaps: parsedResponse.featureGaps || []
    };
}


export async function generateCodeSnippet(testCase: TestCase): Promise<string> {
    const ai = getAiClient();
    const prompt = `
        Based on the following test case, generate a relevant code snippet.
        If it's an API test, generate a cURL command. If it's a UI test, suggest a Cypress or Playwright command.

        Test Case Title: ${testCase.title}
        Description: ${testCase.description}
        Steps:
        ${testCase.steps.join('\n')}

        Expected Results:
        ${testCase.expectedResults.join('\n')}

        Generate only the code snippet as a raw string.
    `;

    const response = await ai.models.generateContent({
        model: "gemini-2.5-flash",
        contents: prompt,
    });

    return response.text.trim();
}

export async function suggestAssertions(testCase: TestCase): Promise<string[]> {
    const ai = getAiClient();
    const prompt = `
        Based on the following test case steps and expected results, suggest a list of 3-5 concise, specific assertions that could be automated.
        Return the response as a JSON array of strings.

        Test Case Title: ${testCase.title}
        Steps:
        ${testCase.steps.join('\n')}
        Expected Results:
        ${testCase.expectedResults.join('\n')}

        Example response: ["expect(response.status).toBe(200)", "expect(toastMessage).toBeVisible()", "expect(user.role).toEqual('admin')"]
    `;
    
    const response = await ai.models.generateContent({
        model: "gemini-2.5-flash",
        contents: prompt,
        config: {
            responseMimeType: "application/json",
            responseSchema: {
                type: Type.ARRAY,
                items: {
                    type: Type.STRING
                }
            }
        }
    });

    try {
        const jsonText = response.text.trim();
        return JSON.parse(jsonText);
    } catch (e) {
        console.error("Failed to parse assertion suggestions:", e);
        return ["Could not generate suggestions."];
    }
}