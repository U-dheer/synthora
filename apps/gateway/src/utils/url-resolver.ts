import { ServicesConfig } from '../config/services.config';

export const resolveServiceUrl = (path: string): string => {
  if (path.startsWith('/auth')) {
    const url = ServicesConfig.auth;
    console.log('Auth service URL:', url);
    if (!url) throw new Error('Auth service URL is not configured');
    return url;
  }
  if (path.startsWith('/gemini')) {
    const url = ServicesConfig.gemini;
    if (!url) throw new Error('Gemini service URL is not configured');
    return url;
  }
  if (path.startsWith('/cohere')) {
    const url = ServicesConfig.cohere;
    if (!url) throw new Error('Cohere service URL is not configured');
    return url;
  }
  if (path.startsWith('/llama')) {
    const url = ServicesConfig.llama;
    if (!url) throw new Error('Llama service URL is not configured');
    return url;
  }
  if (path.startsWith('/summarize')) {
    const url = ServicesConfig.summarizer;
    if (!url) throw new Error('Summarizer service URL is not configured');
    return url;
  }
  if (path.startsWith('/api/summarize')) {
    const url = ServicesConfig.summarizer;
    if (!url) throw new Error('Summarizer service URL is not configured');
    return url;
  }
  if (path.startsWith('/rag')) {
    const url = ServicesConfig.rag;
    if (!url) throw new Error('RAG service URL is not configured');
    return url;
  }
  throw new Error(`No matching service found for path: ${path}`);
};
