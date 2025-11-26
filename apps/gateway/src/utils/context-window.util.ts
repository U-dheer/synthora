export class ContextWindowBuilder {
  private systemPrompt: string = '';
  private question: string = '';
  private fileText: string = '';
  private ragChunks: string[] = [];

  setSystemPrompt(prompt: string) {
    this.systemPrompt = prompt;
    return this;
  }

  setQuestion(question: string) {
    this.question = question;
    return this;
  }
  addRagChunks(chunks: string[]) {
    this.ragChunks = chunks;
    return this;
  }

  build(): string {
    return `
SYSTEM INSTRUCTIONS:
${this.systemPrompt}

USER QUESTION:
${this.question}



UPLOADED FILE CONTENT:
${this.ragChunks.join('\n\n')}
`;
  }
}
