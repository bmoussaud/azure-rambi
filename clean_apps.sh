  az containerapp delete --name gui-svc -g rambi-dev  --no-wait -yy
  az containerapp delete --name movie-generator-svc -g rambi-dev  --no-wait -y
  az containerapp delete --name rambi-events-handler -g rambi-dev  --no-wait -y
  az containerapp delete --name movie-poster-svc -g rambi-dev  --no-wait -y
