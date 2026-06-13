from custom_components.daikin_infrared.rate_limit import SendRateLimiter


def test_first_send_has_no_delay():
    limiter = SendRateLimiter(minimum_interval=1.5)

    assert limiter.delay_until_next_send(now=10.0) == 0


def test_send_inside_minimum_interval_is_delayed():
    limiter = SendRateLimiter(minimum_interval=1.5)
    limiter.mark_sent(now=10.0)

    assert limiter.delay_until_next_send(now=10.5) == 1.0


def test_send_after_minimum_interval_has_no_delay():
    limiter = SendRateLimiter(minimum_interval=1.5)
    limiter.mark_sent(now=10.0)

    assert limiter.delay_until_next_send(now=11.5) == 0
    assert limiter.delay_until_next_send(now=12.0) == 0

