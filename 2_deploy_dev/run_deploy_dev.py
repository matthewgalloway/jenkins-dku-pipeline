import dataikuapi
import sys
import time

# Get parameters from command line
design_url = sys.argv[1]
design_api_key = sys.argv[2]
dss_project = sys.argv[3]
api_service_id = sys.argv[4]
api_package_id = sys.argv[5]
infra_dev_id = sys.argv[6]

# Connect to Design node
client_design = dataikuapi.DSSClient(design_url, design_api_key)
api_deployer = client_design.get_apideployer()

# Get the API service from the deployer
deployer_service = api_deployer.get_service(api_service_id)
print(f"Found existing Deployer API service ({api_service_id})")

# Check for existing deployments
print(f"Looking for existing deployments of '{api_service_id}' on infrastructure '{infra_dev_id}'")
dep_id = f"{api_service_id}-on-{infra_dev_id}"
existing_deployments = [d for d in api_deployer.list_deployments() if d.id == dep_id]

if not existing_deployments:
    print("CREATING DEPLOYMENT")
    dep_to_update = api_deployer.create_deployment(dep_id, deployer_service.id, infra_dev_id, api_package_id)
else:
    print(f"Found deployment to update -> {dep_id}")
    dep_to_update = existing_deployments[0]
    print("UPDATING DEPLOYMENT")

# Get current status before update
current_status = dep_to_update.get_status()
print(f"Current deployment '{dep_id}' on infra '{infra_dev_id}' with API package '{dep_to_update.get_settings().get_raw()['publishedProjectVersion']}' is in status '{current_status.get_health()}'")

# Update deployment settings
dep_settings = dep_to_update.get_settings()
dep_settings.set_single_version(api_package_id)
dep_settings.save()

# Start the update
update_exec = dep_to_update.start_update()
print(f"Update launched -> {update_exec.get_state()}")

# Wait for completion with retry logic for long-running deployments
max_wait_time = 600  # 10 minutes
check_interval = 10  # Check every 10 seconds
start_time = time.time()

while time.time() - start_time < max_wait_time:
    try:
        state = update_exec.get_state()
        
        if state.get('hasResult', False):
            # Deployment completed
            result = update_exec.wait_for_result()
            print(f"  --> Update done with result => {result}")
            break
            
        # Still in progress
        progress = state.get('progress', {}).get('report', {})
        status_msg = progress.get('deploymentHookExecutionStatus', {}).get('deploymentStatusMessage', 'In progress...')
        print(f"  --> Status: {status_msg}")
        
        time.sleep(check_interval)
        
    except Exception as e:
        # Handle connection errors during polling
        print(f"  --> Connection error while checking status (will retry): {e}")
        time.sleep(check_interval)
        continue

# Check final status
try:
    deployment_status = dep_to_update.get_status()
    health = deployment_status.get_health()
    
    print(f"New deployment '{dep_id}' on infra '{infra_dev_id}' with API version '{api_package_id}' is in status '{health}'")
    
    if health == "ERROR":
        print("Deployment failed, aborting")
        sys.exit(1)
    elif health == "HEALTHY":
        print("Deployment successful")
        sys.exit(0)
    else:
        print(f"Deployment in unexpected state: {health}")
        sys.exit(1)
        
except Exception as e:
    print(f"Error checking final deployment status: {e}")
    print("Deployment may still be in progress - check Dataiku UI")
    sys.exit(1)