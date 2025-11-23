"""Tests for multi-dataset validation"""

import pytest
from app.graph_params import GraphParams
from app.validation import GraphDataValidator


@pytest.fixture
def validator():
    """Create a validator instance"""
    return GraphDataValidator()


def test_validation_requires_at_least_one_dataset(validator):
    """Test that at least one dataset (y1 or y) is required"""
    with pytest.raises(ValueError, match="At least one dataset"):
        GraphParams(
            title="No Dataset",
            x=[1, 2, 3],
            # No y or y1 provided
        )


def test_validation_mismatched_dataset_lengths(validator):
    """Test validation fails when datasets have different lengths"""
    params = GraphParams(
        title="Mismatched Lengths",
        y1=[10, 20, 15],
        y2=[8, 18],  # Different length
    )

    result = validator.validate(params)
    assert not result.is_valid
    assert any("same length" in error.message.lower() for error in result.errors)


def test_validation_x_length_mismatch(validator):
    """Test validation fails when x length doesn't match dataset length"""
    params = GraphParams(
        title="X Length Mismatch",
        x=[1, 2, 3, 4, 5],  # 5 points
        y1=[10, 20, 15],  # 3 points
    )

    result = validator.validate(params)
    assert not result.is_valid
    assert any("x array must match" in error.message.lower() for error in result.errors)


def test_validation_all_datasets_same_length(validator):
    """Test validation passes when all datasets have same length"""
    params = GraphParams(
        title="Same Lengths",
        x=[1, 2, 3, 4, 5],
        y1=[10, 20, 15, 25, 30],
        y2=[8, 18, 13, 23, 28],
        y3=[12, 22, 17, 27, 32],
    )

    result = validator.validate(params)
    assert result.is_valid


def test_validation_empty_dataset(validator):
    """Test validation fails with empty dataset"""
    params = GraphParams(
        title="Empty Dataset",
        y1=[],  # Empty
    )

    result = validator.validate(params)
    assert not result.is_valid
    assert any("cannot be empty" in error.message.lower() for error in result.errors)


def test_validation_invalid_color_format(validator):
    """Test validation fails with invalid color format"""
    params = GraphParams(
        title="Invalid Color",
        y1=[10, 20, 15],
        color1="not-a-color",
    )

    result = validator.validate(params)
    assert not result.is_valid
    assert any("invalid color" in error.message.lower() for error in result.errors)


def test_validation_multiple_colors_valid(validator):
    """Test validation passes with valid colors for multiple datasets"""
    params = GraphParams(
        title="Valid Colors",
        y1=[10, 20, 15],
        y2=[8, 18, 13],
        y3=[12, 22, 17],
        color1="red",
        color2="#FF5733",
        color3="rgb(255,87,51)",
    )

    result = validator.validate(params)
    assert result.is_valid


def test_validation_multiple_colors_one_invalid(validator):
    """Test validation fails if any color is invalid"""
    params = GraphParams(
        title="One Invalid Color",
        y1=[10, 20, 15],
        y2=[8, 18, 13],
        y3=[12, 22, 17],
        color1="red",
        color2="invalid-color",
        color3="blue",
    )

    result = validator.validate(params)
    assert not result.is_valid
    assert any("color2" in error.field.lower() for error in result.errors)


def test_validation_line_chart_minimum_points(validator):
    """Test line chart requires at least 2 points"""
    params = GraphParams(
        title="Single Point Line",
        y1=[10],  # Only 1 point
        type="line",
    )

    result = validator.validate(params)
    assert not result.is_valid
    assert any("at least 2" in error.message.lower() for error in result.errors)


def test_validation_scatter_single_point_allowed(validator):
    """Test scatter plot allows single point"""
    params = GraphParams(
        title="Single Point Scatter",
        y1=[10],  # Single point is OK for scatter
        type="scatter",
    )

    result = validator.validate(params)
    assert result.is_valid


def test_validation_auto_x_axis(validator):
    """Test validation passes when x is omitted (auto-generated)"""
    params = GraphParams(
        title="Auto X-axis",
        y1=[10, 20, 15, 25, 30],
        y2=[8, 18, 13, 23, 28],
    )

    result = validator.validate(params)
    assert result.is_valid

    # Verify x-axis is auto-generated
    x_values = params.get_x_values(len(params.y1))  # type: ignore[arg-type]
    assert x_values == [0, 1, 2, 3, 4]


def test_validation_five_datasets_all_valid(validator):
    """Test validation with maximum 5 datasets"""
    params = GraphParams(
        title="Five Datasets",
        y1=[10, 20, 15],
        y2=[8, 18, 13],
        y3=[12, 22, 17],
        y4=[9, 19, 14],
        y5=[11, 21, 16],
    )

    result = validator.validate(params)
    assert result.is_valid


def test_validation_five_datasets_one_wrong_length(validator):
    """Test validation fails if one of five datasets has wrong length"""
    params = GraphParams(
        title="Five Datasets Wrong Length",
        y1=[10, 20, 15],
        y2=[8, 18, 13],
        y3=[12, 22, 17],
        y4=[9, 19, 14],
        y5=[11, 21],  # Wrong length
    )

    result = validator.validate(params)
    assert not result.is_valid
    assert any("same length" in error.message.lower() for error in result.errors)


def test_validation_alpha_range(validator):
    """Test validation of alpha parameter"""
    # Valid alpha
    params1 = GraphParams(
        title="Valid Alpha",
        y1=[10, 20, 15],
        alpha=0.5,
    )
    result1 = validator.validate(params1)
    assert result1.is_valid

    # Invalid alpha (too high)
    params2 = GraphParams(
        title="Invalid Alpha High",
        y1=[10, 20, 15],
        alpha=1.5,
    )
    result2 = validator.validate(params2)
    assert not result2.is_valid

    # Invalid alpha (negative)
    params3 = GraphParams(
        title="Invalid Alpha Negative",
        y1=[10, 20, 15],
        alpha=-0.5,
    )
    result3 = validator.validate(params3)
    assert not result3.is_valid


def test_get_datasets_method(validator):
    """Test the get_datasets() helper method"""
    params = GraphParams(
        title="Get Datasets Test",
        y1=[10, 20, 15],
        y2=[8, 18, 13],
        y3=[12, 22, 17],
        label1="A",
        label2="B",
        label3="C",
        color1="red",
        color2="blue",
        color3="green",
    )

    datasets = params.get_datasets()

    # Should return 3 datasets
    assert len(datasets) == 3

    # Check first dataset
    assert datasets[0][0] == [10, 20, 15]  # y1 data
    assert datasets[0][1] == "A"  # label1
    assert datasets[0][2] == "red"  # color1

    # Check second dataset
    assert datasets[1][0] == [8, 18, 13]  # y2 data
    assert datasets[1][1] == "B"  # label2
    assert datasets[1][2] == "blue"  # color2

    # Check third dataset
    assert datasets[2][0] == [12, 22, 17]  # y3 data
    assert datasets[2][1] == "C"  # label3
    assert datasets[2][2] == "green"  # color3


def test_get_x_values_method(validator):
    """Test the get_x_values() helper method"""
    # With explicit x values
    params1 = GraphParams(
        title="Explicit X",
        x=[1, 2, 3, 4, 5],
        y1=[10, 20, 15, 25, 30],
    )
    x_values1 = params1.get_x_values(5)
    assert x_values1 == [1, 2, 3, 4, 5]

    # Without x values (auto-generated)
    params2 = GraphParams(
        title="Auto X",
        y1=[10, 20, 15, 25, 30],
    )
    x_values2 = params2.get_x_values(5)
    assert x_values2 == [0, 1, 2, 3, 4]


def test_backward_compatibility_mapping(validator):
    """Test backward compatibility parameter mapping"""
    params = GraphParams(
        title="Backward Compatible",
        y=[10, 20, 15],  # Old parameter
        color="blue",  # Old parameter
    )

    # Verify mapping occurred
    assert params.y1 == [10, 20, 15]
    assert params.color1 == "blue"

    # Validation should pass
    result = validator.validate(params)
    assert result.is_valid
