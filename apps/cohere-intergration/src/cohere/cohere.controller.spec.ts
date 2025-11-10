import { Test, TestingModule } from '@nestjs/testing';
import { CohereController } from './cohere.controller';
import { CohereService } from './cohere.service';

describe('CohereController', () => {
  let controller: CohereController;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [CohereController],
      providers: [
        {
          provide: CohereService,
          useValue: {
            make: jest.fn(),
          },
        },
      ],
    }).compile();

    controller = module.get<CohereController>(CohereController);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });
});
