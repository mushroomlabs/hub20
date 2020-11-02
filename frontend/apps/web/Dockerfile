# base image
FROM node:12.2.0-alpine

# set working directory
WORKDIR /app/apps/web

# add `/app/node_modules/.bin` to $PATH
ENV PATH /app/node_modules/.bin:$PATH

# Copy all relevant files into the image
COPY ./apps/web /app/apps/web
COPY ./libs/vue-hub20 /app/libs/vue-hub20

# install and cache app dependencies
RUN npm install /app/libs/vue-hub20
RUN npm install /app/apps/web
RUN npm install @vue/cli -g

# start app
CMD ["npm", "run", "serve"]