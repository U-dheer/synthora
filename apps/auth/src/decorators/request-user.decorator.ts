import { createParamDecorator, ExecutionContext } from '@nestjs/common';

export const RequestUser = createParamDecorator(
  (_data: unknown, ctx: ExecutionContext) => {
    const request = ctx.switchToHttp().getRequest();
    const user = request?.user;
    if (user)
      return user.id ?? (user._id as any) ?? (user.userId as any) ?? null;

    return (request?.userId as any) ?? null;
  },
);
