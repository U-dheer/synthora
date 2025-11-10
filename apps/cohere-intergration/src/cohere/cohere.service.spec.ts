import { Test, TestingModule } from '@nestjs/testing';
import { CohereService } from './cohere.service';
import { ConfigService } from '@nestjs/config';

describe('CohereService', () => {
  let service: CohereService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        CohereService,
        {
          provide: ConfigService,
          useValue: {
            get: jest.fn((key: string) => {
              if (key === 'COHERE_API_KEY') return 'test-api-key';
              if (key === 'COHERE_MODEL') return 'command-r-plus';
              return null;
            }),
          },
        },
      ],
    }).compile();

    service = module.get<CohereService>(CohereService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });
});
