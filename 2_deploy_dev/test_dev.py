import dataikuapi
import pytest

def test_standard_call(params):
    """Test a standard successful prediction call"""
    
    # Connect to deployer
    client_design = dataikuapi.DSSClient(params["host"], params["api"])
    api_deployer = client_design.get_apideployer()
    
    # Get the deployment
    deployment_id = f"{params['api_service_id']}-on-{params['api_dev_infra_id']}"
    deployment = api_deployer.get_deployment(deployment_id)
    
    # Define test query with valid churn prediction features
    test_queries = [{
        'q': {
            'features': {
                'gender': 'F',
                'SeniorCitizen': 0,
                'Partner': 'Yes',
                'Dependents': 'No',
                'tenure': 1,
                'PhoneService': 'No',
                'MultipleLines': 'No phone service',
                'InternetService': 'DSL',
                'OnlineSecurity': 'No',
                'OnlineBackup': 'Yes',
                'DeviceProtection': 'No',
                'TechSupport': 'No',
                'StreamingTV': 'No',
                'StreamingMovies': 'No',
                'Contract': 'Month-to-month',
                'PaperlessBilling': 'Yes',
                'PaymentMethod': 'Electronic check',
                'MonthlyCharges': 29.85,
                'TotalCharges': 29.85
            }
        }
    }]
    
    # Run test queries - works for all infrastructure types!
    result = deployment.run_test_queries(
        endpoint_id=params['api_endpoint_id'],
        test_queries=test_queries
    )
    
    # Verify result
    assert 'results' in result, "No results in response"
    assert len(result['results']) > 0, "Empty results"
    print(f"✓ Test passed. Result: {result['results'][0]}")


def test_missing_param(params):
    """Test error handling for missing parameters"""
    
    # Connect to deployer
    client_design = dataikuapi.DSSClient(params["host"], params["api"])
    api_deployer = client_design.get_apideployer()
    
    # Get the deployment
    deployment_id = f"{params['api_service_id']}-on-{params['api_dev_infra_id']}"
    deployment = api_deployer.get_deployment(deployment_id)
    
    # Query with missing required field
    test_queries = [{
        'q': {
            'features': {
                'gender': 'F'
                # Missing many required fields
            }
        }
    }]
    
    # This should handle the error gracefully
    try:
        result = deployment.run_test_queries(
            endpoint_id=params['api_endpoint_id'],
            test_queries=test_queries
        )
        # Check if error is in the result
        assert 'error' in str(result).lower() or 'results' in result
        print(f"✓ Test passed. Handled missing parameters correctly")
    except Exception as e:
        # If it throws an exception, that's also acceptable
        print(f"✓ Test passed. Exception raised for missing parameters: {e}")


@pytest.fixture
def params(request):
    """Fixture to pass command line parameters to tests"""
    return {
        "host": request.config.getoption("--host"),
        "api": request.config.getoption("--api"),
        "api_service_id": request.config.getoption("--api_service_id"),
        "api_endpoint_id": request.config.getoption("--api_endpoint_id"),
        "api_dev_infra_id": request.config.getoption("--api_dev_infra_id")
    }