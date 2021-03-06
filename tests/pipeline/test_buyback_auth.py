"""
Tests for the reference loader for Buyback Authorizations.
"""
import blaze as bz
from blaze.compute.core import swap_resources_into_scope
import pandas as pd
from six import iteritems

from zipline.pipeline.common import(
    BUYBACK_ANNOUNCEMENT_FIELD_NAME,
    CASH_FIELD_NAME,
    DAYS_SINCE_PREV,
    PREVIOUS_BUYBACK_ANNOUNCEMENT,
    PREVIOUS_BUYBACK_CASH,
    PREVIOUS_BUYBACK_SHARE_COUNT,
    SHARE_COUNT_FIELD_NAME,
    SID_FIELD_NAME,
    TS_FIELD_NAME
)
from zipline.pipeline.data import (
    CashBuybackAuthorizations,
    ShareBuybackAuthorizations
)
from zipline.pipeline.factors.events import (
    BusinessDaysSinceCashBuybackAuth,
    BusinessDaysSinceShareBuybackAuth
)
from zipline.pipeline.loaders.buyback_auth import (
    CashBuybackAuthorizationsLoader,
    ShareBuybackAuthorizationsLoader
)
from zipline.pipeline.loaders.blaze import (
    BlazeCashBuybackAuthorizationsLoader,
    BlazeShareBuybackAuthorizationsLoader,
)
from zipline.pipeline.loaders.utils import (
    zip_with_floats,
    zip_with_dates
)
from zipline.testing.fixtures import (
    WithPipelineEventDataLoader, ZiplineTestCase
)

date_intervals = [
    [['2014-01-01', '2014-01-04'], ['2014-01-05', '2014-01-09'],
     ['2014-01-10', '2014-01-31']]
]

buyback_authorizations_cases = [
    pd.DataFrame({
        SHARE_COUNT_FIELD_NAME: [1, 15],
        CASH_FIELD_NAME: [10, 20],
        TS_FIELD_NAME: pd.to_datetime(['2014-01-05', '2014-01-10']),
        BUYBACK_ANNOUNCEMENT_FIELD_NAME: pd.to_datetime(['2014-01-04',
                                                         '2014-01-09'])
    }),
    pd.DataFrame(
        columns=[SHARE_COUNT_FIELD_NAME,
                 CASH_FIELD_NAME,
                 BUYBACK_ANNOUNCEMENT_FIELD_NAME,
                 TS_FIELD_NAME],
        dtype='datetime64[ns]'
    ),
]


class CashBuybackAuthLoaderTestCase(WithPipelineEventDataLoader,
                                    ZiplineTestCase):
    """
    Test for cash buyback authorizations dataset.
    """
    pipeline_columns = {
        PREVIOUS_BUYBACK_CASH:
            CashBuybackAuthorizations.cash_amount.latest,
        PREVIOUS_BUYBACK_ANNOUNCEMENT:
            CashBuybackAuthorizations.announcement_date.latest,
        DAYS_SINCE_PREV:
            BusinessDaysSinceCashBuybackAuth(),
    }

    @classmethod
    def get_sids(cls):
        return range(2)

    @classmethod
    def get_dataset(cls):
        return {sid:
                frame.drop(SHARE_COUNT_FIELD_NAME, axis=1)
                for sid, frame
                in enumerate(buyback_authorizations_cases)}

    loader_type = CashBuybackAuthorizationsLoader

    def setup(self, dates):
        cols = {
            PREVIOUS_BUYBACK_CASH: self.get_sids_to_frames(zip_with_floats,
                                                           [['NaN', 10, 20]],
                                                           date_intervals,
                                                           dates),
            PREVIOUS_BUYBACK_ANNOUNCEMENT: self.get_sids_to_frames(
                zip_with_dates,
                [['NaT', '2014-01-04', '2014-01-09']],
                date_intervals,
                dates),
        }
        cols[DAYS_SINCE_PREV] = self._compute_busday_offsets(
            cols[PREVIOUS_BUYBACK_ANNOUNCEMENT]
        )
        return cols


class ShareBuybackAuthLoaderTestCase(WithPipelineEventDataLoader,
                                     ZiplineTestCase):
    """
    Test for share buyback authorizations dataset.
    """
    pipeline_columns = {
        PREVIOUS_BUYBACK_SHARE_COUNT:
            ShareBuybackAuthorizations.share_count.latest,
        PREVIOUS_BUYBACK_ANNOUNCEMENT:
            ShareBuybackAuthorizations.announcement_date.latest,
        DAYS_SINCE_PREV:
            BusinessDaysSinceShareBuybackAuth(),
    }

    @classmethod
    def get_sids(cls):
        return range(2)

    @classmethod
    def get_dataset(cls):
        return {sid:
                frame.drop(CASH_FIELD_NAME, axis=1)
                for sid, frame
                in enumerate(buyback_authorizations_cases)}

    loader_type = ShareBuybackAuthorizationsLoader

    def setup(self, dates):
        cols = {PREVIOUS_BUYBACK_SHARE_COUNT:
                self.get_sids_to_frames(zip_with_floats,
                                        [['NaN', 1, 15]],
                                        date_intervals,
                                        dates,),
                PREVIOUS_BUYBACK_ANNOUNCEMENT:
                self.get_sids_to_frames(zip_with_dates,
                                        [['NaT', '2014-01-04', '2014-01-09']],
                                        date_intervals,
                                        dates,),
                }

        cols[DAYS_SINCE_PREV] = self._compute_busday_offsets(
            cols[PREVIOUS_BUYBACK_ANNOUNCEMENT]
        )
        return cols


class BlazeCashBuybackAuthLoaderTestCase(CashBuybackAuthLoaderTestCase):
    """ Test case for loading via blaze.
    """
    loader_type = BlazeCashBuybackAuthorizationsLoader

    def pipeline_event_loader_args(self, dates):
        _, mapping = super(
            BlazeCashBuybackAuthLoaderTestCase,
            self,
        ).pipeline_event_loader_args(dates)
        return (bz.data(pd.concat(
            pd.DataFrame({
                BUYBACK_ANNOUNCEMENT_FIELD_NAME:
                    frame[BUYBACK_ANNOUNCEMENT_FIELD_NAME],
                CASH_FIELD_NAME:
                    frame[CASH_FIELD_NAME],
                TS_FIELD_NAME:
                    frame[TS_FIELD_NAME],
                SID_FIELD_NAME: sid,
            })
            for sid, frame in iteritems(mapping)
        ).reset_index(drop=True)),)


class BlazeShareBuybackAuthLoaderTestCase(ShareBuybackAuthLoaderTestCase):
    """ Test case for loading via blaze.
    """
    loader_type = BlazeShareBuybackAuthorizationsLoader

    def pipeline_event_loader_args(self, dates):
        _, mapping = super(
            BlazeShareBuybackAuthLoaderTestCase,
            self,
        ).pipeline_event_loader_args(dates)
        return (bz.data(pd.concat(
            pd.DataFrame({
                BUYBACK_ANNOUNCEMENT_FIELD_NAME:
                    frame[BUYBACK_ANNOUNCEMENT_FIELD_NAME],
                SHARE_COUNT_FIELD_NAME:
                    frame[SHARE_COUNT_FIELD_NAME],
                TS_FIELD_NAME:
                    frame[TS_FIELD_NAME],
                SID_FIELD_NAME: sid,
            })
            for sid, frame in iteritems(mapping)
        ).reset_index(drop=True)),)


class BlazeShareBuybackAuthLoaderNotInteractiveTestCase(
        BlazeShareBuybackAuthLoaderTestCase):
    """Test case for passing a non-interactive symbol and a dict of resources.
    """
    def pipeline_event_loader_args(self, dates):
        (bound_expr,) = super(
            BlazeShareBuybackAuthLoaderNotInteractiveTestCase,
            self,
        ).pipeline_event_loader_args(dates)
        return swap_resources_into_scope(bound_expr, {})


class BlazeCashBuybackAuthLoaderNotInteractiveTestCase(
        BlazeCashBuybackAuthLoaderTestCase):
    """Test case for passing a non-interactive symbol and a dict of resources.
    """
    def pipeline_event_loader_args(self, dates):
        (bound_expr,) = super(
            BlazeCashBuybackAuthLoaderNotInteractiveTestCase,
            self,
        ).pipeline_event_loader_args(dates)
        return swap_resources_into_scope(bound_expr, {})
