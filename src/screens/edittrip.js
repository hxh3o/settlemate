import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import MemberTable from './membertable';

function Login() {
	let navigate = useNavigate();
	let location = useLocation();
	const [tripName, setTripName] = useState('');
	const [ownerId, setOwnerId] = useState('');

	useEffect(() => {
		async function authorize() {
			const authToken = localStorage.getItem('authToken');
			if (!authToken) navigate('/profile');
			else fetchData();
			async function fetchData() {
				try {
					const response = await fetch(`${process.env.REACT_APP_API_URL}/getMinTripData`, {
						method: 'POST',
						headers: {
							'Content-Type': 'application/json',
						},
						body: JSON.stringify({
							token: localStorage.getItem('authToken'),
							tripid: location.state.tripid,
						}),
					});
					const json = await response.json();
					if (json.success) {
						if (json.data.owner !== json.userId)
							navigate('/trip', {
								state: { tripid: location.state.tripid },
							});
						setTripName(json.data.name);
						setOwnerId(json.data.owner);
						// console.log(json);
						// console.log(data);
					} else {
						json.errors.forEach(error => {
							toast.error(error.msg, {});
						});
						if (json.logout === true) {
							localStorage.removeItem('authToken');
							localStorage.setItem('forcedLogOut', true);
							navigate('/profile');
						}
					}
				} catch (error) {
					console.error('Error fetching trip Data :', error);
				}
			}
		}
		authorize();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

	const updateName = async () => {
		const response = await fetch(`${process.env.REACT_APP_API_URL}/updateTripName`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				token: localStorage.getItem('authToken'),
				tripid: location.state.tripid,
				name: tripName,
			}),
		});
		const json = await response.json();
		// console.log(json);
		if (!json.success) {
			json.errors.forEach(error => {
				toast.error(error.msg, {});
			});
			if (json.logout === true) {
				localStorage.removeItem('authToken');
				localStorage.setItem('forcedLogOut', true);
				navigate('/profile');
			}
		} else {
			toast.success('Trip Name Updates!', {});
		}
	};

	return (
		<div>
			<div
				style={{
					display: 'flex',
					gap: '20px',
					alignItems: 'center',
					padding: '20px',
					justifyContent: 'center',
				}}
			>
				<div>
					<Button
						onClick={() =>
							navigate('/trip', {
								state: { tripid: location.state.tripid },
							})
						}
						variant='contained'
					>
						Back to Trip
					</Button>
				</div>
				<div>
					<TextField type='text' id='tripName' value={tripName} label='Trip Name' onChange={e => setTripName(e.target.value)} />
				</div>
				<div>
					<Button onClick={updateName} variant='contained'>
						Save
					</Button>
				</div>
			</div>
			<MemberTable tripid={location.state.tripid} ownerId={ownerId} />
		</div>
	);
}

export default Login;
