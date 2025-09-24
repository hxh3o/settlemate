import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { API, authHeaders } from '../api';
import 'react-toastify/dist/ReactToastify.css';
import InviteTable from './inviteTable.js';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';

function Profile() {
	let navigate = useNavigate();
	const [data, setData] = useState({});

	useEffect(() => {
		async function authorize() {
			const authToken = localStorage.getItem('authToken');
			if (!authToken) navigate('/');
			else fetchData();
		}
		async function fetchData() {
			try {
                const response = await fetch(`${API}/getUserData`, {
                    method: 'GET',
                    headers: authHeaders(),
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
						navigate('/');
					}
				} else {
					if (json.newAuthToken) localStorage.setItem('authToken', json.newAuthToken);
					setData(json.data);
					// console.log(json.data);
				}
			} catch (error) {
				console.error('Error fetching data :', error);
			}
		}
		authorize();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);
	return (
		<div
			style={{
				display: 'flex',
				justifyContent: 'center',
				alignItems: 'center',
				height: '100vh',
			}}
		>
			<div>
				<Typography variant='h4' style={{ textAlign: 'center' }}>
					{data.name}
				</Typography>
				<Typography variant='h5' style={{ textAlign: 'center' }}>
					{data.email}
				</Typography>
				<Typography variant='h5' style={{ textAlign: 'center' }}>
					{data.upi}
				</Typography>
				<div style={{ display: 'flex', justifyContent: 'center', padding: '10px' }}>
					<Button variant='contained' onClick={() => navigate('/editprofile')}>
						Edit Profile
					</Button>
				</div>
				<br></br>
				<InviteTable />
			</div>
		</div>
	);
}

export default Profile;
