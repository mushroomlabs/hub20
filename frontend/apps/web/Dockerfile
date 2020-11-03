# base image
FROM node:12.2.0-alpine

# set working directory
WORKDIR /app/apps/web

# add `/app/node_modules/.bin` to $PATH
ENV PATH /app/apps/web/node_modules/.bin:/app/libs/node_modules/.bin:$PATH

# Copy all relevant files into the image
COPY ./apps/web /app/apps/web
COPY ./libs/vue-hub20 /app/libs/vue-hub20

# install and cache app dependencies
RUN npm install .
RUN npm link /app/libs/vue-hub20
RUN npm install @vue/cli

# start app
CMD ["vue-cli-service", "serve", "--watch"]