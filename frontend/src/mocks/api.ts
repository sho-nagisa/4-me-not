import { mockPersons, mockCommunities } from "./data";

export const api = {
  getPersons: async () => {
    return mockPersons;
  },

  getCommunities: async () => {
    return mockCommunities;
  },

  createInteraction: async (payload: any) => {
    console.log("mock create interaction:", payload);
    return { status: "ok" };
  },
};
