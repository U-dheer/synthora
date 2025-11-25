import { Injectable, HttpException, Logger } from '@nestjs/common';
import axios from 'axios';
import { resolveServiceUrl } from '../utils/url-resolver';
import { ServicesConfig } from '../config/services.config';

// In-memory backoff tracking for Gemini quota errors
let lastGemini429At = 0;
const GEMINI_BACKOFF_MS = 60 * 1000; // 60 seconds

@Injectable()
export class GatewayService {
  async handleAIRequest(question: string, incomingHeaders?: any) {
    try {
      console.log('Handling AI request for question:', question);
      console.log('Calling AI models...');
      console.log('Gemini URL:', `${ServicesConfig.gemini}/gemini/make`);
      console.log('Cohere URL:', `${ServicesConfig.cohere}/cohere/make`);
      console.log('Llama URL:', `${ServicesConfig.llama}/hugging-face/chat`);

      // Prepare the request body in the format expected by the AI services (PromptDto)
      const requestBody = { input: question };

      // Call the three AI models concurrently but tolerate failures
      // Build promises for each AI call, skipping Gemini if it's in backoff
      const now = Date.now();
      const geminiInBackoff = now - lastGemini429At < GEMINI_BACKOFF_MS;

      // Build per-service outbound headers. If the gateway has an API key
      // configured for the target LLM, prefer that key (Bearer) over the
      // incoming user's Authorization header. This allows the gateway to
      // authenticate to downstream LLM backends which expect a dedicated
      // API key while still supporting per-user forwarding when keys are
      // not configured.
      const geminiKey = (ServicesConfig as any).geminiApiKey;
      const geminiHeaderName =
        (ServicesConfig as any).geminiApiKeyHeader || 'Authorization';
      let geminiOutboundAuth: any = incomingHeaders?.authorization;
      if (geminiKey) {
        const headerLower = String(geminiHeaderName).toLowerCase();
        geminiOutboundAuth =
          headerLower === 'authorization' ? `Bearer ${geminiKey}` : geminiKey;
      }

      const geminiHeaders: any = {
        'Content-Type': 'application/json',
      };
      if (geminiOutboundAuth)
        geminiHeaders[geminiHeaderName] = geminiOutboundAuth;

      const geminiPromise = geminiInBackoff
        ? Promise.resolve({ data: null, skipped: true })
        : axios.post(`${ServicesConfig.gemini}/gemini/make`, requestBody, {
            headers: geminiHeaders,
          });

      const cohereKey = (ServicesConfig as any).cohereApiKey;
      const cohereHeaderName =
        (ServicesConfig as any).cohereApiKeyHeader || 'Authorization';
      let cohereOutboundAuth: any = incomingHeaders?.authorization;
      if (cohereKey) {
        const headerLower = String(cohereHeaderName).toLowerCase();
        cohereOutboundAuth =
          headerLower === 'authorization' ? `Bearer ${cohereKey}` : cohereKey;
      }

      const cohereHeaders: any = {
        'Content-Type': 'application/json',
      };
      if (cohereOutboundAuth)
        cohereHeaders[cohereHeaderName] = cohereOutboundAuth;

      const coherePromise = axios.post(
        `${ServicesConfig.cohere}/cohere/make`,
        requestBody,
        {
          headers: cohereHeaders,
        },
      );

      const llamaKey = (ServicesConfig as any).llamaApiKey;
      const llamaHeaderName =
        (ServicesConfig as any).llamaApiKeyHeader || 'Authorization';
      let llamaOutboundAuth: any = incomingHeaders?.authorization;
      if (llamaKey) {
        const headerLower = String(llamaHeaderName).toLowerCase();
        llamaOutboundAuth =
          headerLower === 'authorization' ? `Bearer ${llamaKey}` : llamaKey;
      }

      const llamaHeaders: any = {
        'Content-Type': 'application/json',
      };
      if (llamaOutboundAuth) llamaHeaders[llamaHeaderName] = llamaOutboundAuth;

      const llamaPromise = axios.post(
        `${ServicesConfig.llama}/hugging-face/chat`,
        requestBody,
        {
          headers: llamaHeaders,
        },
      );

      const settled = await Promise.allSettled([
        geminiPromise,
        coherePromise,
        llamaPromise,
      ]);

      // Normalize results: if a call failed, store the error instead of throwing
      const geminiRes =
        settled[0].status === 'fulfilled'
          ? settled[0].value
          : { error: settled[0].reason };
      const cohereRes =
        settled[1].status === 'fulfilled'
          ? settled[1].value
          : { error: settled[1].reason };
      const llamaRes =
        settled[2].status === 'fulfilled'
          ? settled[2].value
          : { error: settled[2].reason };

      // Cast to any for more ergonomic logging/inspection
      const geminiAny: any = geminiRes;
      const cohereAny: any = cohereRes;
      const llamaAny: any = llamaRes;

      // If Gemini returned a quota error, enable short backoff
      try {
        const geminiErrorStatus =
          geminiAny?.error?.response?.status || geminiAny?.error?.status;
        if (geminiErrorStatus === 429) {
          lastGemini429At = Date.now();
          console.log(
            'Gemini returned 429 -> enabling backoff for',
            GEMINI_BACKOFF_MS,
            'ms',
          );
        }
        if (geminiAny?.skipped) {
          console.log('Gemini call skipped due to backoff');
        }
      } catch (e) {
        // ignore inspection errors
      }

      console.log('AI model call results:', {
        gemini: geminiAny.error
          ? `ERROR: ${geminiAny.error.message || geminiAny.error}`
          : 'OK',
        cohere: cohereAny.error
          ? `ERROR: ${cohereAny.error.message || cohereAny.error}`
          : 'OK',
        llama: llamaAny.error
          ? `ERROR: ${llamaAny.error.message || llamaAny.error}`
          : 'OK',
      });

      const responses = {
        ai1: geminiAny.error ? geminiAny.error : geminiAny.data,
        ai2: cohereAny.error ? cohereAny.error : cohereAny.data,
        ai3: llamaAny.error ? llamaAny.error : llamaAny.data,
      };

      console.log('AI model responses received');
      console.log('Sending to summarizer...');

      // Try to summarize, but if it fails, use the first AI response (Gemini)
      let summary;
      try {
        // Send all to summarizer (note: the endpoint is /api/summarize/ai-prompts)
        // The summarizer expects ai1, ai2, ai3 as strings
        // Normalize summarizer base URL (strip any accidental '/summarize' suffix)
        const summarizerBase = (ServicesConfig.summarizer || '')
          .replace(/\/summarize\/?$/i, '')
          .replace(/\/$/, '');

        console.log('Summarizer base URL:', summarizerBase);

        const summaryRes = await axios.post(
          `${summarizerBase}/api/summarize/ai-prompts`,
          {
            ai1:
              typeof geminiAny.data === 'string'
                ? geminiAny.data
                : JSON.stringify(geminiAny.data),
            ai2:
              typeof cohereAny.data === 'string'
                ? cohereAny.data
                : JSON.stringify(cohereAny.data),
            ai3:
              typeof llamaAny.data === 'string'
                ? llamaAny.data
                : JSON.stringify(llamaAny.data),
          },
        );

        console.log('✅ Summarizer responded successfully!');
        summary = summaryRes.data;
      } catch (summarizerError) {
        console.log(
          '⚠️ Summarizer unavailable, using first available AI response',
        );
        // Prefer a successful model in order: Cohere, Llama, Gemini
        let fallbackData: any = null;
        if (!cohereAny.error) fallbackData = cohereAny.data;
        else if (!llamaAny.error) fallbackData = llamaAny.data;
        else if (!geminiAny.error) fallbackData = geminiAny.data;
        else
          fallbackData = geminiAny.error || cohereAny.error || llamaAny.error;

        if (fallbackData?.response) {
          summary = fallbackData.response;
        } else if (fallbackData?.message?.content) {
          summary = fallbackData.message.content;
        } else if (typeof fallbackData === 'string') {
          summary = fallbackData;
        } else {
          summary = JSON.stringify(fallbackData);
        }
      }

      return {
        summary: summary,
        rawResponses: responses,
      };
    } catch (error) {
      console.error('Error in handleAIRequest:', error.message);
      console.error('Error details:', error.response?.data);
      console.error('Error status:', error.response?.status);
      throw new HttpException(
        error.response?.data?.message || error.message,
        error.response?.status || 500,
      );
    }
  }

  async forwardRequest(
    method: string,
    path: string,
    body?: any,
    headers?: any,
  ) {
    try {
      const serviceUrl = resolveServiceUrl(path);
      console.log('Resolved service URL:', serviceUrl);

      // Remove the service prefix from the path to avoid duplication
      // e.g., incoming path: /gemini/gemini/make -> forwarded path: /gemini/make
      let forwardedPath = path;
      if (path.startsWith('/gemini')) {
        forwardedPath = path.replace(/^\/gemini/, '');
      } else if (path.startsWith('/cohere')) {
        forwardedPath = path.replace(/^\/cohere/, '');
      } else if (path.startsWith('/llama')) {
        forwardedPath = path.replace(/^\/llama/, '');
      }

      // Build candidate forwarded paths. To preserve backwards compatibility
      // with deployments that mounted auth controllers either at `/auth` or
      // at the root, attempt the original incoming path first and on a 404
      // retry using the stripped '/auth' prefix. This avoids breaking the
      // previous strip behavior while preferring the explicit path.
      const candidatePaths: string[] = [forwardedPath];
      if (path.startsWith('/auth')) {
        const stripped = path.replace(/^\/auth/, '') || '/';
        // If stripped path is different, add as fallback
        if (stripped !== forwardedPath) candidatePaths.push(stripped);
      }

      const serviceUrlNormalized = serviceUrl.endsWith('/')
        ? serviceUrl.slice(0, -1)
        : serviceUrl;

      let lastError: any = null;
      for (const cand of candidatePaths) {
        const targetUrl = `${serviceUrlNormalized}${cand}`;
        console.log('Forwarding request to:', targetUrl);
        console.log('Request method:', method);
        console.log('Request body:', body);
        try {
          console.log('Making axios request...');
          // Forward incoming headers where appropriate. Do not force
          // application/json since that breaks multipart/form-data uploads.
          const forwardedHeaders: any = {
            Accept: headers?.['accept'] || '*/*',
            // Forward authentication headers
            ...(headers?.['authorization'] && {
              Authorization: headers['authorization'],
            }),
            ...(headers?.['cookie'] && { Cookie: headers['cookie'] }),
          };

          // Preserve Content-Type if provided (important for multipart)
          if (headers?.['content-type']) {
            forwardedHeaders['Content-Type'] = headers['content-type'];
          }

          const response = await axios.request({
            method,
            url: targetUrl,
            data: body,
            headers: forwardedHeaders,
            timeout: 30000, // 30 second timeout for better debugging
            // Allow large bodies when forwarding files
            maxBodyLength: Infinity,
            maxContentLength: Infinity,
          });

          console.log('Response received from target service:', response.data);
          // Successful response, proceed as before
          // Special handling for RAG queries with no knowledge base data
          if (
            path.includes('/rag/query') &&
            response.data.no_kb_data === true
          ) {
            console.log(
              '⚠️ No knowledge base data found - orchestrating AI models...',
            );
            const question = body?.question || body?.query;

            if (!question) {
              return response.data;
            }

            try {
              // Call the 3 AI models and get summarized response
              const aiResponse = await this.handleAIRequest(question, headers);

              // Store the summarized response in vector DB via RAG service
              console.log('📝 Storing AI response in knowledge base...');
              await axios
                .post(`${serviceUrl}/rag/documents/text`, {
                  content: aiResponse.summary,
                  metadata: {
                    source: 'ai_generated',
                    question: question,
                    timestamp: new Date().toISOString(),
                    models_used: ['gemini', 'cohere', 'llama'],
                  },
                })
                .catch((err) => {
                  console.error('⚠️ Failed to store in KB:', err.message);
                  // Don't fail the request if storage fails
                });

              // Return the AI-generated response to user
              return {
                answer: aiResponse.summary,
                query_type: 'ai_generated',
                retrieved_contexts: [],
                llm_responses: [
                  { service: 'gemini', response: aiResponse.rawResponses.ai1 },
                  { service: 'cohere', response: aiResponse.rawResponses.ai2 },
                  { service: 'llama', response: aiResponse.rawResponses.ai3 },
                ],
                processing_time_seconds: 0,
                timestamp: new Date().toISOString(),
              };
            } catch (aiError) {
              console.error('❌ AI orchestration failed:', aiError.message);
              // Return original RAG response if AI fails
              return response.data;
            }
          }

          return response.data;
        } catch (error) {
          lastError = error;
          // If target responded 404, try the next candidate path; otherwise bubble up
          const status = error?.response?.status;
          console.error('Error forwarding to', targetUrl, 'status:', status);
          if (status === 404) {
            console.warn(
              'Received 404 from target, trying next candidate path if available',
            );
            continue; // try next candidate
          }
          console.error('Error in forwardRequest:', error.message);
          console.error('Error details:', error.response?.data);
          console.error('Error status:', status);
          console.error('Full error:', error);
          throw new HttpException(
            error.response?.data?.message || error.message,
            status || 500,
          );
        }
      }

      // If we exit the loop with no successful response, throw last error
      if (lastError) {
        throw new HttpException(
          lastError.response?.data?.message || lastError.message,
          lastError.response?.status || 500,
        );
      }

      // All forwarding attempts exhausted (either returned earlier or thrown)
    } catch (error) {
      console.error('Error in forwardRequest:', error.message);
      console.error('Error details:', error.response?.data);
      console.error('Error status:', error.response?.status);
      console.error('Full error:', error);
      throw new HttpException(
        error.response?.data?.message || error.message,
        error.response?.status || 500,
      );
    }
  }
}
