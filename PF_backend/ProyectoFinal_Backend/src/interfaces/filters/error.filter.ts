import { ArgumentsHost, Catch, ExceptionFilter, HttpException, HttpStatus } from '@nestjs/common';

@Catch()
export class AllErrorsFilter implements ExceptionFilter {
  catch(exception: any, host: ArgumentsHost) {
    const res = host.switchToHttp().getResponse();
    if (exception instanceof HttpException) {
      const status = exception.getStatus();
      return res.status(status).json({ error: exception.message });
    }
    console.error(exception);
    return res.status(HttpStatus.INTERNAL_SERVER_ERROR).json({ error: 'internal_error' });
  }
}
