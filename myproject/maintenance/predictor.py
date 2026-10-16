from statistics import median


class ServiceIntervalPredictor:
    """پیش‌بینی فاصله سرویس فقط از روی تاریخچه زمانی."""

    MIN_INTERVAL_DAYS = 30
    MAX_INTERVAL_DAYS = 1095

    @classmethod
    def predict(cls, matching_events, *, fallback_days):
        events = sorted(
            matching_events or [],
            key=lambda event: event.timestamp,
        )

        date_gaps = []
        for previous, current in zip(events, events[1:]):
            day_gap = (current.date - previous.date).days
            if day_gap > 0:
                date_gaps.append(day_gap)

        predicted_days = fallback_days
        source = "rule"
        confidence = 0.50

        if date_gaps:
            predicted_days = int(round(median(date_gaps)))
            predicted_days = max(
                cls.MIN_INTERVAL_DAYS,
                min(cls.MAX_INTERVAL_DAYS, predicted_days),
            )
            source = "history"
            confidence = min(0.95, 0.60 + (0.08 * len(date_gaps)))

        return {
            "interval_days": predicted_days,
            "source": source,
            "confidence": confidence,
            "samples": len(date_gaps),
        }
