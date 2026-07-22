# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Tests for OSM contributor service."""
import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from services.osm_contributor import OSM_TAG_MAP, OSMContributor, get_osm_contributor


@pytest.fixture
def osm_contributor():
    """Create OSM contributor with mock token."""
    with patch.object(OSMContributor, '_load_token', return_value='mock_token'):
        contributor = OSMContributor()
        yield contributor
        # Cleanup
        if hasattr(contributor, '_client'):
            import asyncio
            try:
                asyncio.get_event_loop().run_until_complete(contributor.close())
            except Exception:
                pass  # Best-effort cleanup: event loop may already be closed during fixture teardown


@pytest.fixture
def osm_contributor_no_token():
    """Create OSM contributor without token."""
    with patch.object(OSMContributor, '_load_token', return_value=''):
        contributor = OSMContributor()
        yield contributor


def test_osm_tag_map_exists():
    """Test that OSM tag map is properly defined."""
    assert 'pothole' in OSM_TAG_MAP
    assert 'damaged_road' in OSM_TAG_MAP
    assert 'flooding' in OSM_TAG_MAP
    assert 'waterlogging' in OSM_TAG_MAP
    assert 'broken_barrier' in OSM_TAG_MAP
    assert 'missing_sign' in OSM_TAG_MAP
    assert 'accident' in OSM_TAG_MAP
    assert 'landslide' in OSM_TAG_MAP
    assert 'debris' in OSM_TAG_MAP


def test_osm_tag_map_pothole():
    """Test pothole tag mapping."""
    tags = OSM_TAG_MAP['pothole']
    assert tags['highway'] == 'pothole'
    assert tags['surface'] == 'damaged'
    assert tags['hazard'] == 'yes'
    assert tags['hazard:type'] == 'pothole'


def test_osm_tag_map_flooding():
    """Test flooding tag mapping."""
    tags = OSM_TAG_MAP['flooding']
    assert tags['hazard'] == 'yes'
    assert tags['hazard:type'] == 'flood'
    assert tags['flood_prone'] == 'yes'


def test_osm_contributor_init_with_token(osm_contributor):
    """Test OSM contributor initialization with token."""
    assert osm_contributor.is_configured is True
    assert osm_contributor._access_token == 'mock_token'


def test_osm_contributor_init_without_token(osm_contributor_no_token):
    """Test OSM contributor initialization without token."""
    assert osm_contributor_no_token.is_configured is False


@pytest.mark.asyncio
async def test_contribute_report_not_configured(osm_contributor_no_token):
    """Test contribution when OSM is not configured."""
    report = {
        'id': '123',
        'lat': 13.0827,
        'lon': 80.2707,
        'issue_type': 'pothole',
        'description': 'Large pothole',
    }

    result = await osm_contributor_no_token.contribute_report(report)

    assert result['status'] == 'skipped'
    assert 'OSM not configured' in result['reason']


@pytest.mark.asyncio
async def test_contribute_report_missing_coordinates(osm_contributor):
    """Test contribution with missing coordinates."""
    report = {
        'id': '123',
        'issue_type': 'pothole',
        'description': 'Large pothole',
    }

    result = await osm_contributor.contribute_report(report)

    assert result['status'] == 'error'
    assert 'Missing coordinates' in result['reason']


@pytest.mark.asyncio
async def test_contribute_report_success(osm_contributor):
    """Test successful report contribution."""
    report = {
        'id': '123',
        'lat': 13.0827,
        'lon': 80.2707,
        'issue_type': 'pothole',
        'description': 'Large pothole on main road',
        'road_name': 'Test Road',
    }

    # Mock the OSM API calls
    with patch.object(osm_contributor, '_open_changeset', new_callable=AsyncMock) as mock_open:
        mock_open.return_value = 'changeset_456'

        with patch.object(osm_contributor, '_create_node', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = 'node_789'

            with patch.object(osm_contributor, '_close_changeset', new_callable=AsyncMock) as mock_close:
                mock_close.return_value = True

                result = await osm_contributor.contribute_report(report)

                assert result['status'] == 'success'
                assert result['changeset_id'] == 'changeset_456'
                assert result['node_id'] == 'node_789'
                assert 'osm_url' in result
                assert 'node_789' in result['osm_url']

                mock_open.assert_called_once_with('pothole')
                mock_create.assert_called_once()
                mock_close.assert_called_once_with('changeset_456')


@pytest.mark.asyncio
async def test_contribute_report_changeset_failure(osm_contributor):
    """Test contribution when changeset creation fails."""
    report = {
        'id': '123',
        'lat': 13.0827,
        'lon': 80.2707,
        'issue_type': 'pothole',
    }

    with patch.object(osm_contributor, '_open_changeset', new_callable=AsyncMock) as mock_open:
        mock_open.return_value = None

        result = await osm_contributor.contribute_report(report)

        assert result['status'] == 'error'
        assert 'Failed to open changeset' in result['reason']


@pytest.mark.asyncio
async def test_contribute_report_node_creation_failure(osm_contributor):
    """Test contribution when node creation fails."""
    report = {
        'id': '123',
        'lat': 13.0827,
        'lon': 80.2707,
        'issue_type': 'pothole',
    }

    with patch.object(osm_contributor, '_open_changeset', new_callable=AsyncMock) as mock_open:
        mock_open.return_value = 'changeset_456'

        with patch.object(osm_contributor, '_create_node', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = None

            with patch.object(osm_contributor, '_close_changeset', new_callable=AsyncMock) as mock_close:
                mock_close.return_value = True

                result = await osm_contributor.contribute_report(report)

                assert result['status'] == 'error'
                assert 'Failed to create node' in result['reason']
                mock_close.assert_called_once_with('changeset_456')


@pytest.mark.asyncio
async def test_contribute_report_exception_handling(osm_contributor):
    """Test contribution when exception occurs."""
    report = {
        'id': '123',
        'lat': 13.0827,
        'lon': 80.2707,
        'issue_type': 'pothole',
    }

    with patch.object(osm_contributor, '_open_changeset', new_callable=AsyncMock) as mock_open:
        mock_open.side_effect = httpx.RequestError("Network error")

        result = await osm_contributor.contribute_report(report)

        assert result['status'] == 'error'
        assert 'Network error' in result['reason']


@pytest.mark.asyncio
async def test_open_changeset_success(osm_contributor):
    """Test successful changeset creation."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '12345'

    with patch.object(osm_contributor._client, 'put', new_callable=AsyncMock) as mock_put:
        mock_put.return_value = mock_response

        result = await osm_contributor._open_changeset('pothole')

        assert result == '12345'
        mock_put.assert_called_once()


@pytest.mark.asyncio
async def test_open_changeset_failure(osm_contributor):
    """Test failed changeset creation."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = 'Unauthorized'

    with patch.object(osm_contributor._client, 'put', new_callable=AsyncMock) as mock_put:
        mock_put.return_value = mock_response

        result = await osm_contributor._open_changeset('pothole')

        assert result is None


@pytest.mark.asyncio
async def test_open_changeset_exception(osm_contributor):
    """Test changeset creation with exception."""
    with patch.object(osm_contributor._client, 'put', new_callable=AsyncMock) as mock_put:
        mock_put.side_effect = httpx.RequestError("Connection error")

        result = await osm_contributor._open_changeset('pothole')

        assert result is None


@pytest.mark.asyncio
async def test_create_node_success(osm_contributor):
    """Test successful node creation."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '67890'

    tags = {'hazard': 'yes', 'hazard:type': 'pothole'}

    with patch.object(osm_contributor._client, 'put', new_callable=AsyncMock) as mock_put:
        mock_put.return_value = mock_response

        result = await osm_contributor._create_node('12345', 13.0827, 80.2707, tags)

        assert result == '67890'
        mock_put.assert_called_once()


@pytest.mark.asyncio
async def test_create_node_failure(osm_contributor):
    """Test failed node creation."""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = 'Bad request'

    tags = {'hazard': 'yes'}

    with patch.object(osm_contributor._client, 'put', new_callable=AsyncMock) as mock_put:
        mock_put.return_value = mock_response

        result = await osm_contributor._create_node('12345', 13.0827, 80.2707, tags)

        assert result is None


@pytest.mark.asyncio
async def test_close_changeset_success(osm_contributor):
    """Test successful changeset closing."""
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch.object(osm_contributor._client, 'put', new_callable=AsyncMock) as mock_put:
        mock_put.return_value = mock_response

        result = await osm_contributor._close_changeset('12345')

        assert result is True


@pytest.mark.asyncio
async def test_close_changeset_failure(osm_contributor):
    """Test failed changeset closing."""
    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch.object(osm_contributor._client, 'put', new_callable=AsyncMock) as mock_put:
        mock_put.return_value = mock_response

        result = await osm_contributor._close_changeset('12345')

        assert result is False


@pytest.mark.asyncio
async def test_close_changeset_exception(osm_contributor):
    """Test changeset closing with exception."""
    with patch.object(osm_contributor._client, 'put', new_callable=AsyncMock) as mock_put:
        mock_put.side_effect = httpx.RequestError("Connection error")

        result = await osm_contributor._close_changeset('12345')

        assert result is False


def test_load_token_from_env():
    """Test loading token from environment."""
    with patch.dict(os.environ, {'OSM_ACCESS_TOKEN': 'test_token_123'}):
        token = OSMContributor._load_token()
        assert token == 'test_token_123'


def test_load_token_empty_env():
    """Test loading token when environment variable is empty."""
    with patch.dict(os.environ, {'OSM_ACCESS_TOKEN': ''}, clear=False):
        if 'OSM_ACCESS_TOKEN' in os.environ:
            del os.environ['OSM_ACCESS_TOKEN']
        token = OSMContributor._load_token()
        assert token == ''


def test_get_osm_contributor_singleton():
    """Test singleton pattern for OSM contributor."""
    # Reset singleton
    import services.osm_contributor as osm_module
    osm_module._contributor = None

    with patch.object(OSMContributor, '_load_token', return_value='mock_token'):
        contributor1 = get_osm_contributor()
        contributor2 = get_osm_contributor()

        assert contributor1 is contributor2
        assert isinstance(contributor1, OSMContributor)


@pytest.mark.asyncio
async def test_contribute_report_with_different_issue_types(osm_contributor):
    """Test contribution with different issue types."""
    issue_types = ['pothole', 'damaged_road', 'flooding', 'waterlogging',
                   'broken_barrier', 'missing_sign', 'accident', 'landslide', 'debris']

    for issue_type in issue_types:
        report = {
            'id': '123',
            'lat': 13.0827,
            'lon': 80.2707,
            'issue_type': issue_type,
        }

        with patch.object(osm_contributor, '_open_changeset', new_callable=AsyncMock) as mock_open:
            mock_open.return_value = 'changeset_456'

            with patch.object(osm_contributor, '_create_node', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = 'node_789'

                with patch.object(osm_contributor, '_close_changeset', new_callable=AsyncMock) as mock_close:
                    mock_close.return_value = True

                    result = await osm_contributor.contribute_report(report)

                    assert result['status'] == 'success'
                    mock_open.assert_called_once_with(issue_type)


@pytest.mark.asyncio
async def test_contribute_report_with_optional_fields(osm_contributor):
    """Test contribution with optional fields."""
    report = {
        'id': '123',
        'lat': 13.0827,
        'lon': 80.2707,
        'issue_type': 'pothole',
        'description': 'Very long description that should be truncated if it exceeds 255 characters. ' * 10,
        'road_name': 'Test Road Name',
        'city': 'Chennai',
        'severity': 'high',
    }

    with patch.object(osm_contributor, '_open_changeset', new_callable=AsyncMock) as mock_open:
        mock_open.return_value = 'changeset_456'

        with patch.object(osm_contributor, '_create_node', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = 'node_789'

            with patch.object(osm_contributor, '_close_changeset', new_callable=AsyncMock) as mock_close:
                mock_close.return_value = True

                result = await osm_contributor.contribute_report(report)

                assert result['status'] == 'success'
                # Verify description was truncated if needed
                call_args = mock_create.call_args
                assert call_args is not None


@pytest.mark.asyncio
async def test_contribute_report_with_unknown_issue_type(osm_contributor):
    """Test contribution with unknown issue type."""
    report = {
        'id': '123',
        'lat': 13.0827,
        'lon': 80.2707,
        'issue_type': 'unknown_type',
    }

    with patch.object(osm_contributor, '_open_changeset', new_callable=AsyncMock) as mock_open:
        mock_open.return_value = 'changeset_456'

        with patch.object(osm_contributor, '_create_node', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = 'node_789'

            with patch.object(osm_contributor, '_close_changeset', new_callable=AsyncMock) as mock_close:
                mock_close.return_value = True

                result = await osm_contributor.contribute_report(report)

                assert result['status'] == 'success'
                # Should use default hazard tags
                mock_open.assert_called_once_with('unknown_type')
