resource "aws_cloudwatch_log_group" "application" {
  name              = "/aws/elasticbeanstalk/${var.project_name}-${var.environment}/application"
  retention_in_days = 7
}

resource "aws_sns_topic" "alarms" {
  name = "${var.project_name}-${var.environment}-alarms"
}

resource "aws_sns_topic_subscription" "alarm_email" {
  count = var.alarm_email == null ? 0 : 1

  topic_arn = aws_sns_topic.alarms.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

resource "aws_cloudwatch_metric_alarm" "environment_health" {
  alarm_name          = "${var.project_name}-${var.environment}-degraded-health"
  alarm_description   = "Elastic Beanstalk environment health is not OK."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "EnvironmentHealth"
  namespace           = "AWS/ElasticBeanstalk"
  period              = 300
  statistic           = "Maximum"
  threshold           = 0
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alarms.arn]

  dimensions = {
    EnvironmentName = aws_elastic_beanstalk_environment.backend.name
  }
}
