export const sampleRequirements = `
As a registered user, I want to be able to log in to the application using my email and password, so that I can access my personalized content.`;

export const sampleOpenAPISchema = `{
openapi: 3.0.0
info:
  title: Simple Login API
  version: 1.0.0
paths:
  /login:
    post:
      summary: User login
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                  format: email
                password:
                  type: string
                  minLength: 8
      responses:
        '200':
          description: Login successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  token:
                    type: string
        '401':
          description: Unauthorized
}
`;
