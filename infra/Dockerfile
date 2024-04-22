FROM nginx:1.22.1
COPY nginx.conf /etc/nginx/templates/default.conf.template
RUN mkdir -p api/docs
COPY openapi-schema.yml api/docs
COPY redoc.html api/docs
