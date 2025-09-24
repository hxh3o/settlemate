import React, { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import 'react-toastify/dist/ReactToastify.css';
import TransferTable from './transferTable';

import Button from '@mui/material/Button';

function Transfer() {
	let navigate = useNavigate();
	let location = useLocation();

	useEffect(() => {
		async function authorize() {
			const authToken = localStorage.getItem('authToken');
			if (!authToken) navigate('/profile');
		}
		authorize();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

	return (
		<div>
			<div style={{ position: 'relative' }}>
				<div
					style={{
						position: 'absolute',
						top: 0,
						left: 0,
						zIndex: 1,
						width: '100%',
					}}
				>
					<TransferTable tripid={location.state.tripid} />
				</div>
				<div
					className='lol'
					style={{
						position: 'absolute',
						top: 0,
						left: 0,
						zIndex: 10,
						padding: '10px',
						display: 'flex',
						gap: '10px',
					}}
				>
					<Button
						onClick={() =>
							navigate('/trip', {
								state: { tripid: location.state.tripid },
							})
						}
						variant='contained'
					>
						Back To Trip
					</Button>
				</div>
			</div>
		</div>
	);
}

export default Transfer;
