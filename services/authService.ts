import { User } from '../types';

const mockUsers: User[] = [
    { id: '1', email: 'user1@test.com' },
    { id: '2', email: 'user2@test.com' },
];

// In a real app, this would be a secure API call.
// Here we simulate it with a delay.
export const login = (email: string, password?: string): Promise<User> => {
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            if (!email) {
                return reject(new Error('Email address is required.'));
            }
            
            // Find an existing user
            let user = mockUsers.find(u => u.email.toLowerCase() === email.toLowerCase());
            
            // If user doesn't exist, create a new one on-the-fly.
            if (!user) {
                user = {
                    id: `user-${Date.now()}`,
                    email: email,
                };
            }
            
            // We are ignoring the password for this mock implementation
            resolve(user);
        }, 1000);
    });
};